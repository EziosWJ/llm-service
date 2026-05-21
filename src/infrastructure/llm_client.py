"""LLM 客户端封装，基于 OpenAI SDK 对接上游大模型服务。"""

from __future__ import annotations

import logging
from typing import Iterator

from openai import APIConnectionError, APITimeoutError, OpenAI

from src.models.errors import UpstreamError

logger = logging.getLogger(__name__)


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
        # enable_thinking: 是否开启模型深度思考模式（部分模型支持）
        self.model = model
        self.enable_thinking = enable_thinking
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key or "EMPTY",
            timeout=timeout,
        )

    def generate(self, prompt: str) -> str:
        """同步调用 LLM，返回完整文本结果。"""

        logger.info("LLM request: prompt_length=%d, model=%s", len(prompt), self.model)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                extra_body={"enable_thinking": self.enable_thinking},
            )
        except (APITimeoutError, APIConnectionError) as exc:
            logger.error("LLM upstream failure: %s", exc)
            raise UpstreamError("LLM upstream timeout or connection failure") from exc

        choice = response.choices[0] if response.choices else None
        if choice and choice.message and choice.message.content:
            logger.info("LLM response: text_length=%d", len(choice.message.content))
            return choice.message.content
        logger.warning("LLM returned empty response")
        return ""

    def generate_stream(self, prompt: str) -> Iterator[str]:
        """流式调用 LLM，逐块 yield 文本片段（用于 SSE 实时推送）。"""

        logger.info("LLM stream request: prompt_length=%d, model=%s", len(prompt), self.model)
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                extra_body={"enable_thinking": self.enable_thinking},
                stream=True,
            )
        except (APITimeoutError, APIConnectionError) as exc:
            logger.error("LLM upstream failure: %s", exc)
            raise UpstreamError("LLM upstream timeout or connection failure") from exc

        try:
            for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content
        except (APITimeoutError, APIConnectionError) as exc:
            logger.error("LLM stream interrupted: %s", exc)
            raise UpstreamError("LLM stream interrupted") from exc
