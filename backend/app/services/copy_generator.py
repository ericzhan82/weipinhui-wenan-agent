import os

from sqlalchemy.orm import Session

from app.models import CopyOutput, HistoryCase, Product, Rule, ValidationResult
from app.services.copy_validator import validate_copy_payload
from app.services.llm import get_llm_client
from app.services.prompt_builder import build_generation_messages, build_rewrite_messages
from app.services.version_service import create_copy_version


def product_to_dict(product: Product) -> dict:
    return {
        "id": product.id,
        "style_no": product.style_no,
        "product_no": product.product_no,
        "category_3": product.category_3,
        "category_4": product.category_4,
        "age_range": product.age_range,
        "gender": product.gender,
        "season": product.season,
        "scene": product.scene,
        "fba": product.fba,
        "remark": product.remark,
        "skus": [
            {
                "sku_no": sku.sku_no,
                "color_name": sku.color_name,
                "color_code": sku.color_code,
                "color_remark": sku.color_remark,
            }
            for sku in product.skus
        ],
    }


def _rules(db: Session) -> list[Rule]:
    return db.query(Rule).filter(Rule.enabled.is_(True)).all()


def _forbidden_terms(rules: list[Rule]) -> list[str]:
    terms: list[str] = []
    for rule in rules:
        if rule.rule_type == "forbidden":
            terms.extend(line.strip() for line in rule.content.replace("，", "\n").splitlines())
    return [term for term in terms if term]


def _history(db: Session, product: Product) -> list[dict]:
    cases = (
        db.query(HistoryCase)
        .filter(HistoryCase.category_3 == product.category_3)
        .order_by(HistoryCase.created_at.desc())
        .limit(5)
        .all()
    )
    return [
        {"title": item.title, "main_image_tags": item.main_image_tags, "color_copy": item.color_copy}
        for item in cases
    ]


def _upsert_copy_output(
    db: Session,
    product: Product,
    payload: dict,
    operator_name: str,
    version_type: str,
    change_reason: str,
) -> CopyOutput:
    output = db.query(CopyOutput).filter(CopyOutput.product_id == product.id).first()
    client = get_llm_client()
    if not output:
        output = CopyOutput(product_id=product.id, created_by=operator_name)
        db.add(output)
        db.flush()
    output.title = payload.get("title")
    output.main_image_tags = payload.get("main_image_tags") or []
    output.color_copy = payload.get("color_copy")
    output.source_basis = payload.get("source_basis")
    output.llm_provider = client.provider
    output.llm_model = client.model
    output.status = "generated" if version_type == "model_generated" else "edited"
    output.updated_by = operator_name
    product.status = output.status
    product.updated_by = operator_name
    create_copy_version(
        db,
        product.id,
        output,
        version_type,
        output.title or "",
        output.main_image_tags,
        output.color_copy or "",
        operator_name,
        change_reason,
    )
    return output


def generate_copy_for_product(db: Session, product_id: int, operator_name: str = "system") -> dict:
    product = db.get(Product, product_id)
    if not product:
        raise ValueError("商品不存在")
    rules = _rules(db)
    product_payload = product_to_dict(product)
    client = get_llm_client()
    messages = build_generation_messages(product_payload, [rule.content for rule in rules], _history(db, product))
    payload = client.generate_json(messages, schema_hint={"product": product_payload})
    validation = validate_copy_payload(
        payload.get("title"),
        payload.get("main_image_tags"),
        payload.get("color_copy"),
        forbidden_terms=_forbidden_terms(rules),
        required_basis_fields={"fba": product.fba, "category_3": product.category_3},
    )
    if not validation["passed"]:
        if os.getenv("LLM_PROVIDER", "mock") == "mock":
            from app.services.llm.mock_client import MockClient

            payload = MockClient().generate_json(messages, schema_hint={"product": product_payload})
            validation = validate_copy_payload(
                payload.get("title"),
                payload.get("main_image_tags"),
                payload.get("color_copy"),
                forbidden_terms=_forbidden_terms(rules),
                required_basis_fields={"fba": product.fba, "category_3": product.category_3},
            )
        if not validation["passed"]:
            raise ValueError({"message": "文案生成后校验未通过", "validation": validation})
    output = _upsert_copy_output(db, product, payload, operator_name, "model_generated", "模型生成")
    db.add(
        ValidationResult(
            product_id=product.id,
            copy_output_id=output.id,
            passed=validation["passed"],
            errors_json=validation["errors"],
            warnings_json=validation["warnings"] + payload.get("warnings", []),
            checked_by=operator_name,
        )
    )
    db.commit()
    db.refresh(output)
    return {
        "product_id": product.id,
        "title": output.title,
        "main_image_tags": output.main_image_tags,
        "color_copy": output.color_copy,
        "source_basis": output.source_basis,
        "warnings": validation["warnings"] + payload.get("warnings", []),
    }


def rewrite_copy_for_product(db: Session, product_id: int, instruction: str, operator_name: str = "operator") -> dict:
    product = db.get(Product, product_id)
    if not product:
        raise ValueError("商品不存在")
    current = product.copy_output
    if not current:
        return generate_copy_for_product(db, product_id, operator_name)
    rules = _rules(db)
    current_payload = {
        "title": current.title,
        "main_image_tags": current.main_image_tags,
        "color_copy": current.color_copy,
    }
    client = get_llm_client()
    messages = build_rewrite_messages(product_to_dict(product), current_payload, instruction, [rule.content for rule in rules])
    payload = client.generate_json(messages, schema_hint={"product": product_to_dict(product), "current": current_payload})
    if instruction and "防晒" in instruction:
        payload["title"] = payload["title"].replace("舒适", "防晒", 1)
    validation = validate_copy_payload(
        payload.get("title"),
        payload.get("main_image_tags"),
        payload.get("color_copy"),
        forbidden_terms=_forbidden_terms(rules),
        required_basis_fields={"fba": product.fba, "category_3": product.category_3},
    )
    if not validation["passed"]:
        raise ValueError({"message": "重写文案校验未通过", "validation": validation})
    output = _upsert_copy_output(db, product, payload, operator_name, "rewrite", instruction)
    db.commit()
    db.refresh(output)
    return {
        "product_id": product.id,
        "title": output.title,
        "main_image_tags": output.main_image_tags,
        "color_copy": output.color_copy,
        "source_basis": output.source_basis,
        "warnings": validation["warnings"],
    }


def save_manual_copy(
    db: Session,
    product_id: int,
    title: str,
    main_image_tags: list[str],
    color_copy: str,
    operator_name: str,
    change_reason: str,
) -> CopyOutput:
    product = db.get(Product, product_id)
    if not product:
        raise ValueError("商品不存在")
    payload = {
        "title": title,
        "main_image_tags": main_image_tags,
        "color_copy": color_copy,
        "source_basis": "人工编辑保存",
    }
    output = _upsert_copy_output(db, product, payload, operator_name, "manual_edit", change_reason)
    db.commit()
    db.refresh(output)
    return output


def validate_product_copy(
    db: Session,
    product_id: int,
    title: str | None = None,
    main_image_tags: list[str] | None = None,
    color_copy: str | None = None,
    operator_name: str = "operator",
) -> dict:
    product = db.get(Product, product_id)
    if not product:
        raise ValueError("商品不存在")
    output = product.copy_output
    rules = _rules(db)
    result = validate_copy_payload(
        title if title is not None else (output.title if output else ""),
        main_image_tags if main_image_tags is not None else (output.main_image_tags if output else []),
        color_copy if color_copy is not None else (output.color_copy if output else ""),
        forbidden_terms=_forbidden_terms(rules),
        required_basis_fields={"fba": product.fba, "category_3": product.category_3},
    )
    validation = ValidationResult(
        product_id=product.id,
        copy_output_id=output.id if output else None,
        passed=result["passed"],
        errors_json=result["errors"],
        warnings_json=result["warnings"],
        checked_by=operator_name,
    )
    db.add(validation)
    db.commit()
    return result
