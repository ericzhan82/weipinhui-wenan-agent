def build_generation_messages(
    product: dict,
    rules: list[str],
    history_cases: list[dict],
    hot_search_context: dict | None = None,
) -> list[dict]:
    hot_search_text = ""
    if hot_search_context and hot_search_context.get("enabled"):
        hot_search_text = (
            "\n热搜词标题增强：已启用。"
            f"\n可用热搜词：{hot_search_context.get('selected_hot_terms', [])}"
            "\n标题必须优先完整连续包含可用热搜词，不要拆字凑词。"
            f"\n被过滤热搜词及原因：{hot_search_context.get('excluded_hot_terms', [])}"
        )
    return [
        {
            "role": "system",
            "content": (
                "你是唯品童装商品文案助手。只输出一个 JSON 对象，不输出 Markdown。"
                "字段名必须严格使用 title、main_image_tags、color_copy、source_basis、warnings。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请根据商品资料生成唯品标题、主图打标卖点和颜色词文案。"
                "\n输出格式必须为："
                '{"title":"29-30个中文字符","main_image_tags":["4-10个字符","4-10个字符","4-10个字符"],'
                '"color_copy":"4-6个字符","source_basis":"生成依据","warnings":[]}'
                "\n不要使用中文字段名；不要把 JSON 包在 Markdown 代码块里；不要输出解释。"
                f"{hot_search_text}"
                f"\n商品资料：{product}\n规则：{rules}\n历史优秀案例：{history_cases}"
            ),
        },
    ]


def build_rewrite_messages(product: dict, current_copy: dict, instruction: str, rules: list[str]) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "你是唯品童装商品文案改写助手。只输出一个 JSON 对象，不输出 Markdown。"
                "字段名必须严格使用 title、main_image_tags、color_copy、source_basis、warnings。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"商品资料：{product}\n当前文案：{current_copy}\n改写要求：{instruction}\n"
                f"规则：{rules}\n请保持不编造卖点，并满足字数限制："
                "title为29-30个中文字符，main_image_tags每项4-10个字符，color_copy为4-6个字符。"
            ),
        },
    ]
