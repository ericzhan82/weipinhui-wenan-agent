from app.services.copy_validator import validate_copy_payload


def test_validator_accepts_rule_compliant_copy():
    result = validate_copy_payload(
        title="清凉防晒舒适透气中大童女童防晒衣夏季出游轻薄舒适百搭好穿外套",
        main_image_tags=["清凉防晒", "透气不闷", "出游好穿"],
        color_copy="清爽显白",
        forbidden_terms=["最强", "第一"],
        required_basis_fields={"fba": "防晒透气", "category_3": "外套"},
    )

    assert result["passed"] is True
    assert result["errors"] == []


def test_validator_rejects_length_and_forbidden_terms():
    result = validate_copy_payload(
        title="最强防晒衣",
        main_image_tags=["短"],
        color_copy="清",
        forbidden_terms=["最强"],
        required_basis_fields={"fba": "", "category_3": "外套"},
    )

    messages = [item["message"] for item in result["errors"]]
    assert "标题长度不是29-30个字符" in messages
    assert "主图卖点长度必须为4-10个字符" in messages
    assert "颜色词文案长度必须为4-6个字符" in messages
    assert "文案包含禁用词：最强" in messages
    assert "生成依据字段缺失：fba" in messages
