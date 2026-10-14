import json
from typing import Iterator

from openai import OpenAI

from app.config import settings
from app.llm.provider import StreamResult, Usage


class OpenAIProvider:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url or None)
        self.model = settings.llm_model

    def stream(self, system: str, user: str, result: StreamResult) -> Iterator[str]:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0,
            stream=True,
            stream_options={"include_usage": True},   # final chunk carries token usage
        )
        for chunk in response:
            if chunk.usage:
                result.usage = Usage(chunk.usage.prompt_tokens, chunk.usage.completion_tokens)
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def complete_json(self, system: str, user: str, max_tokens: int = 200) -> dict:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content or "{}")


_provider: OpenAIProvider | None = None


def get_provider() -> OpenAIProvider:
    global _provider
    if _provider is None:
        _provider = OpenAIProvider()
    return _provider
