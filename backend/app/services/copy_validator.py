ABSOLUTE_TERMS = ["最强", "最佳", "第一", "顶级", "全网", "永久", "100%", "必买"]


def _length(text: str | None) -> int:
    return len((text or "").strip())


def _as_list(tags: list[str] | None) -> list[str]:
    return [str(tag).strip() for tag in (tags or []) if str(tag).strip()]


def validate_copy_payload(
    title: str | None,
    main_image_tags: list[str] | None,
    color_copy: str | None,
    forbidden_terms: list[str] | None = None,
    required_basis_fields: dict[str, str | None] | None = None,
) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []
    tags = _as_list(main_image_tags)
    title_text = (title or "").strip()
    color_text = (color_copy or "").strip()

    if not title_text:
        errors.append({"field": "title", "message": "标题不能为空", "value": title_text})
    elif _length(title_text) not in (29, 30):
        errors.append({"field": "title", "message": "标题长度不是29-30个字符", "value": title_text})

    if not tags:
        errors.append({"field": "main_image_tags", "message": "主图卖点不能为空", "value": tags})
    for tag in tags:
        if _length(tag) < 4 or _length(tag) > 10:
            errors.append(
                {"field": "main_image_tags", "message": "主图卖点长度必须为4-10个字符", "value": tag}
            )

    if not color_text:
        errors.append({"field": "color_copy", "message": "颜色词文案不能为空", "value": color_text})
    elif _length(color_text) < 4 or _length(color_text) > 6:
        errors.append({"field": "color_copy", "message": "颜色词文案长度必须为4-6个字符", "value": color_text})

    combined = " ".join([title_text, color_text, *tags])
    for term in [term.strip() for term in (forbidden_terms or []) if term.strip()]:
        if term and term in combined:
            errors.append({"field": "copy", "message": f"文案包含禁用词：{term}", "value": term})

    for term in ABSOLUTE_TERMS:
        if term in combined:
            warnings.append({"field": "copy", "message": f"文案包含绝对化风险词：{term}", "value": term})

    for field, value in (required_basis_fields or {}).items():
        if not str(value or "").strip():
            errors.append({"field": field, "message": f"生成依据字段缺失：{field}", "value": value})

    return {"passed": not errors, "errors": errors, "warnings": warnings}
