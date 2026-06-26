from typing import AsyncIterator, List, Tuple

from ..types import ChatMessage, MessageRole


class AnthropicProvider:
    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-6",
        max_tokens: int = 8192,
    ):
        from anthropic import AsyncAnthropic

        # Увеличенный таймаут: мощные модели (Opus) дольше отвечают на длинных промптах
        self._client = AsyncAnthropic(api_key=api_key, timeout=600.0)
        self._model = model
        self._max_tokens = max_tokens

    def _split_messages(
        self, messages: List[ChatMessage]
    ) -> Tuple[str, List[dict]]:
        """Anthropic ожидает system-сообщения отдельным параметром,
        а в messages — только user/assistant."""
        system_parts: List[str] = []
        sdk_messages: List[dict] = []
        for m in messages:
            if m.role == MessageRole.SYSTEM:
                system_parts.append(m.content)
            else:
                sdk_messages.append({"role": m.role.value, "content": m.content})
        return "\n\n".join(system_parts), sdk_messages

    async def stream(self, messages: List[ChatMessage]) -> AsyncIterator[str]:
        system, sdk_messages = self._split_messages(messages)

        kwargs = dict(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=sdk_messages,
        )
        if system:
            kwargs["system"] = system

        async with self._client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text

    async def complete(self, messages: List[ChatMessage]) -> str:
        system, sdk_messages = self._split_messages(messages)

        kwargs = dict(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=sdk_messages,
        )
        if system:
            kwargs["system"] = system

        # Стриминг под капотом: устойчиво к таймаутам на длинных ответах
        # мощных моделей (Opus). Anthropic рекомендует streaming для таких запросов.
        parts: List[str] = []
        async with self._client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                parts.append(text)
        return "".join(parts)
