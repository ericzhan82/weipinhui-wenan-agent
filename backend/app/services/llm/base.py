class LlmClient:
    provider = "base"
    model = "base"

    def generate_json(self, messages: list[dict], schema_hint: dict | None = None) -> dict:
        raise NotImplementedError
