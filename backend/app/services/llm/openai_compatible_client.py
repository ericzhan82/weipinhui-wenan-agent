import json
import os
import re

import requests

from .base import LlmClient


class OpenAICompatibleClient(LlmClient):
    provider = "openai_compatible"

    def __init__(self) -> None:
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.base_url = os.getenv("LLM_BASE_URL", "").rstrip("/")
        self.model = os.getenv("LLM_MODEL", "mock")
        self.timeout = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.4"))

    def generate_json(self, messages: list[dict], schema_hint: dict | None = None) -> dict:
        if not self.api_key or not self.base_url or not self.model:
            raise RuntimeError("openai-compatible模式需要配置LLM_API_KEY、LLM_BASE_URL、LLM_MODEL")

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": self.model, "messages": messages, "temperature": self.temperature},
                timeout=self.timeout,
            )
        except requests.exceptions.Timeout as exc:
            raise RuntimeError(f"模型接口调用超时：{self.timeout}秒内没有返回，请检查模型服务、网络或调低输入复杂度") from exc
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(f"模型接口请求失败：{exc}") from exc
        if response.status_code >= 400:
            raise RuntimeError(f"模型接口调用失败：HTTP {response.status_code}，{response.text[:300]}")
        body = response.json()
        content = body["choices"][0]["message"]["content"]
        return self._parse_json(content)

    @staticmethod
    def _parse_json(content: str) -> dict:
        text = content.strip()
        fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.S)
        if fenced:
            text = fenced.group(1).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"模型输出不是可解析JSON：{exc}") from exc
