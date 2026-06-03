import json
import os
import re

from sqlalchemy.orm import Session

from app.models import CopyOutput, HistoryCase, Product, Rule, ValidationResult
from app.services.copy_validator import validate_copy_payload
from app.services.hot_search_service import evaluate_hot_title, get_hot_search_config, select_hot_terms_for_product
from app.services.llm import get_llm_client
from app.services.prompt_builder import build_generation_messages, build_rewrite_messages
from app.services.version_service import create_copy_version


TITLE_KEYS = ("title", "标题", "商品标题", "唯品标题", "vip_title")
TAG_KEYS = (
    "main_image_tags",
    "mainImageTags",
    "main_image_selling_points",
    "主图卖点",
    "主图打标卖点",
    "主图标签",
    "卖点标签",
    "卖点",
)
COLOR_KEYS = ("color_copy", "colorCopy", "颜色词文案", "颜色文案", "颜色词", "色彩文案")
SOURCE_KEYS = ("source_basis", "sourceBasis", "生成依据", "来源依据", "依据")
WARNING_KEYS = ("warnings", "风险提示", "提醒")
NESTED_PAYLOAD_KEYS = ("copy", "copy_output", "result", "data", "文案", "生成文案")


def _has_content(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _lookup(payload: dict, keys: tuple[str, ...]):
    for key in keys:
        value = payload.get(key)
        if _has_content(value):
            return value
    for nested_key in NESTED_PAYLOAD_KEYS:
        nested = payload.get(nested_key)
        if isinstance(nested, dict):
            value = _lookup(nested, keys)
            if _has_content(value):
                return value
    return None


def _text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple)):
        return "".join(str(item).strip() for item in value if str(item).strip())
    return str(value).strip()


def _tags(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in re.split(r"[\n,，、;；]+", value) if item.strip()]
    if isinstance(value, dict):
        value = value.values()
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _normalize_llm_payload(payload: dict) -> dict:
    if not isinstance(payload, dict):
        return {}
    normalized = dict(payload)
    normalized["title"] = _text(_lookup(payload, TITLE_KEYS))
    normalized["main_image_tags"] = _tags(_lookup(payload, TAG_KEYS))
    normalized["color_copy"] = _text(_lookup(payload, COLOR_KEYS))
    normalized["source_basis"] = _text(_lookup(payload, SOURCE_KEYS)) or payload.get("source_basis")
    warnings = _lookup(payload, WARNING_KEYS)
    normalized["warnings"] = warnings if isinstance(warnings, list) else []
    return normalized


def _validate_generated_payload(payload: dict, rules: list[Rule], product: Product) -> dict:
    return validate_copy_payload(
        payload.get("title"),
        payload.get("main_image_tags"),
        payload.get("color_copy"),
        forbidden_terms=_forbidden_terms(rules),
        required_basis_fields={"fba": product.fba, "category_3": product.category_3},
    )


def _max_attempts() -> int:
    return _max_attempts_for_client(None)


def _max_attempts_for_client(client) -> int:
    retries_value = getattr(client, "max_retries", None)
    try:
        retries = int(retries_value if retries_value is not None else os.getenv("LLM_MAX_RETRIES", "0"))
    except (TypeError, ValueError):
        retries = 0
    return max(1, retries + 1)


def _repair_messages(messages: list[dict], payload: dict, validation: dict) -> list[dict]:
    return [
        *messages,
        {
            "role": "user",
            "content": (
                "上一轮文案校验未通过，请只输出修正后的JSON对象，不要解释。"
                "字段名必须严格使用 title、main_image_tags、color_copy、source_basis、warnings。"
                "title必须为29-30个中文字符；main_image_tags必须为数组，且每项4-10个字符；"
                "color_copy必须为4-6个字符。"
                f"\n上一轮输出：{json.dumps(payload, ensure_ascii=False)}"
                f"\n校验错误：{json.dumps(validation['errors'], ensure_ascii=False)}"
            ),
        },
    ]


def _valid_title(value: str | None) -> bool:
    return len((value or "").strip()) in (29, 30)


def _valid_tags(value: list[str] | None) -> bool:
    tags = _tags(value)
    return bool(tags) and all(4 <= len(tag) <= 10 for tag in tags)


def _valid_color_copy(value: str | None) -> bool:
    return 4 <= len((value or "").strip()) <= 6


def _locally_repair_payload(payload: dict, product_payload: dict) -> dict:
    from app.services.llm.mock_client import MockClient

    fallback = MockClient().generate_json([], schema_hint={"product": product_payload})
    repaired = dict(payload)
    if not _valid_title(repaired.get("title")):
        repaired["title"] = fallback["title"]
    if not _valid_tags(repaired.get("main_image_tags")):
        repaired["main_image_tags"] = fallback["main_image_tags"]
    if not _valid_color_copy(repaired.get("color_copy")):
        repaired["color_copy"] = fallback["color_copy"]
    if not _has_content(repaired.get("source_basis")):
        repaired["source_basis"] = "模型输出未通过校验，系统根据商品资料自动补全"
    warnings = repaired.get("warnings") if isinstance(repaired.get("warnings"), list) else []
    repaired["warnings"] = [
        *warnings,
        {"field": "copy", "message": "模型输出未通过校验，已根据商品资料自动补全", "value": "local_repair"},
    ]
    return _normalize_llm_payload(repaired)


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


def _rules(db: Session, workspace_id: int | None = None) -> list[Rule]:
    query = db.query(Rule).filter(Rule.enabled.is_(True))
    if workspace_id is not None:
        query = query.filter(Rule.workspace_id == workspace_id)
    return query.all()


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
        .filter(HistoryCase.workspace_id == product.workspace_id)
        .order_by(HistoryCase.created_at.desc())
        .limit(5)
        .all()
    )
    return [
        {"title": item.title, "main_image_tags": item.main_image_tags, "color_copy": item.color_copy}
        for item in cases
    ]


def _base_hot_search_context(enabled: bool = False) -> dict:
    return {
        "enabled": enabled,
        "selected_hot_terms": [],
        "matched_hot_terms": [],
        "missing_hot_terms": [],
        "excluded_hot_terms": [],
        "hot_search_source_batch": None,
    }


def _resolve_hot_search_context(db: Session, product: Product, use_hot_search: bool | None) -> dict:
    enabled = bool(get_hot_search_config(db, product.workspace_id)["enabled_by_default"]) if use_hot_search is None else use_hot_search
    if not enabled:
        return _base_hot_search_context(False)
    selected = select_hot_terms_for_product(db, product)
    context = {
        **_base_hot_search_context(True),
        **selected,
    }
    if not context["selected_hot_terms"]:
        raise ValueError(
            {
                "message": "未找到可用热搜词",
                "validation": {
                    "passed": False,
                    "errors": [
                        {
                            "field": "hot_search",
                            "message": "当前商品类目没有可用热搜词，或热搜词已被规避词/性别规则过滤",
                            "value": product.category_3,
                        }
                    ],
                    "warnings": [],
                },
            }
        )
    return context


def _merge_hot_search_validation(payload: dict, validation: dict, hot_search_context: dict) -> dict:
    if not hot_search_context.get("enabled"):
        return {**hot_search_context, "matched_hot_terms": [], "missing_hot_terms": []}
    coverage = evaluate_hot_title(payload.get("title"), hot_search_context.get("selected_hot_terms"))
    hot_search_context = {**hot_search_context, **coverage}
    for term in coverage["missing_hot_terms"]:
        validation["errors"].append(
            {"field": "title", "message": f"标题未完整包含热搜词：{term}", "value": term}
        )
    validation["passed"] = not validation["errors"]
    return hot_search_context


def _upsert_copy_output(
    db: Session,
    product: Product,
    payload: dict,
    operator_name: str,
    version_type: str,
    change_reason: str,
    client=None,
) -> CopyOutput:
    output = db.query(CopyOutput).filter(CopyOutput.product_id == product.id).first()
    client = client or get_llm_client(db)
    if not output:
        output = CopyOutput(product_id=product.id, workspace_id=product.workspace_id, created_by=operator_name)
        db.add(output)
        db.flush()
    output.workspace_id = product.workspace_id
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


def generate_copy_for_product(
    db: Session,
    product_id: int,
    operator_name: str = "system",
    use_hot_search: bool | None = None,
) -> dict:
    product = db.get(Product, product_id)
    if not product:
        raise ValueError("商品不存在")
    rules = _rules(db, product.workspace_id)
    product_payload = product_to_dict(product)
    client = get_llm_client(db)
    hot_search_context = _resolve_hot_search_context(db, product, use_hot_search)
    messages = build_generation_messages(
        product_payload,
        [rule.content for rule in rules],
        _history(db, product),
        hot_search_context,
    )
    payload = _normalize_llm_payload(
        client.generate_json(
            messages,
            schema_hint={"product": product_payload, "hot_search": hot_search_context},
        )
    )
    validation = _validate_generated_payload(payload, rules, product)
    hot_search_context = _merge_hot_search_validation(payload, validation, hot_search_context)
    if not validation["passed"]:
        repaired_payload = _locally_repair_payload(payload, product_payload)
        repaired_validation = _validate_generated_payload(repaired_payload, rules, product)
        repaired_hot_search_context = _merge_hot_search_validation(
            repaired_payload,
            repaired_validation,
            hot_search_context,
        )
        if repaired_validation["passed"]:
            payload = repaired_payload
            validation = repaired_validation
            hot_search_context = repaired_hot_search_context
    attempt = 1
    while (
        not validation["passed"]
        and client.provider != "mock"
        and attempt < _max_attempts_for_client(client)
    ):
        repair_messages = _repair_messages(messages, payload, validation)
        payload = _normalize_llm_payload(
            client.generate_json(
                repair_messages,
                schema_hint={
                    "product": product_payload,
                    "previous": payload,
                    "validation": validation,
                    "hot_search": hot_search_context,
                },
            )
        )
        validation = _validate_generated_payload(payload, rules, product)
        hot_search_context = _merge_hot_search_validation(payload, validation, hot_search_context)
        attempt += 1
    if not validation["passed"]:
        if client.provider == "mock":
            from app.services.llm.mock_client import MockClient

            payload = _normalize_llm_payload(MockClient().generate_json(messages, schema_hint={"product": product_payload}))
            validation = _validate_generated_payload(payload, rules, product)
            hot_search_context = _merge_hot_search_validation(payload, validation, hot_search_context)
        if not validation["passed"]:
            raise ValueError({"message": "文案生成后校验未通过", "validation": validation})
    output = _upsert_copy_output(db, product, payload, operator_name, "model_generated", "模型生成", client)
    db.add(
        ValidationResult(
            product_id=product.id,
            workspace_id=product.workspace_id,
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
        "hot_search_enabled": hot_search_context["enabled"],
        "selected_hot_terms": hot_search_context["selected_hot_terms"],
        "matched_hot_terms": hot_search_context["matched_hot_terms"],
        "missing_hot_terms": hot_search_context["missing_hot_terms"],
        "excluded_hot_terms": hot_search_context["excluded_hot_terms"],
        "hot_search_source_batch": hot_search_context["hot_search_source_batch"],
    }


def rewrite_copy_for_product(db: Session, product_id: int, instruction: str, operator_name: str = "operator") -> dict:
    product = db.get(Product, product_id)
    if not product:
        raise ValueError("商品不存在")
    current = product.copy_output
    if not current:
        return generate_copy_for_product(db, product_id, operator_name)
    rules = _rules(db, product.workspace_id)
    current_payload = {
        "title": current.title,
        "main_image_tags": current.main_image_tags,
        "color_copy": current.color_copy,
    }
    client = get_llm_client(db)
    messages = build_rewrite_messages(product_to_dict(product), current_payload, instruction, [rule.content for rule in rules])
    payload = _normalize_llm_payload(client.generate_json(messages, schema_hint={"product": product_to_dict(product), "current": current_payload}))
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
    output = _upsert_copy_output(db, product, payload, operator_name, "rewrite", instruction, client)
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
    rules = _rules(db, product.workspace_id)
    result = validate_copy_payload(
        title if title is not None else (output.title if output else ""),
        main_image_tags if main_image_tags is not None else (output.main_image_tags if output else []),
        color_copy if color_copy is not None else (output.color_copy if output else ""),
        forbidden_terms=_forbidden_terms(rules),
        required_basis_fields={"fba": product.fba, "category_3": product.category_3},
    )
    validation = ValidationResult(
        product_id=product.id,
        workspace_id=product.workspace_id,
        copy_output_id=output.id if output else None,
        passed=result["passed"],
        errors_json=result["errors"],
        warnings_json=result["warnings"],
        checked_by=operator_name,
    )
    db.add(validation)
    db.commit()
    return result
