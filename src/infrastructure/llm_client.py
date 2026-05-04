from __future__ import annotations

from openai import APIConnectionError, APITimeoutError, OpenAI

from src.models.errors import UpstreamError


class LLMClient:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str | None = None,
        timeout: float = 60.0,
        enable_thinking: bool = False,
    ) -> None:
        self.model = model
        self.enable_thinking = enable_thinking
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key or "EMPTY",
            timeout=timeout,
        )

    def generate(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                extra_body={"enable_thinking": self.enable_thinking},
            )
        except (APITimeoutError, APIConnectionError) as exc:
            raise UpstreamError("LLM upstream timeout or connection failure") from exc

        choice = response.choices[0] if response.choices else None
        if choice and choice.message and choice.message.content:
            return choice.message.content
        return ""
