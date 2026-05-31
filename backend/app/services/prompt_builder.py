def build_generation_messages(product: dict, rules: list[str], history_cases: list[dict]) -> list[dict]:
    return [
        {
            "role": "system",
            "content": "你是唯品童装商品文案助手。只输出JSON，不输出Markdown。",
        },
        {
            "role": "user",
            "content": (
                "请根据商品资料生成唯品标题、主图打标卖点和颜色词文案。"
                f"\n商品资料：{product}\n规则：{rules}\n历史优秀案例：{history_cases}"
            ),
        },
    ]


def build_rewrite_messages(product: dict, current_copy: dict, instruction: str, rules: list[str]) -> list[dict]:
    return [
        {"role": "system", "content": "你是唯品童装商品文案改写助手。只输出JSON，不输出Markdown。"},
        {
            "role": "user",
            "content": (
                f"商品资料：{product}\n当前文案：{current_copy}\n改写要求：{instruction}\n"
                f"规则：{rules}\n请保持不编造卖点，并满足字数限制。"
            ),
        },
    ]
