from typing import AsyncIterator, List

from ..types import ChatMessage


class DeepSeekProvider:
    """Провайдер DeepSeek. API DeepSeek совместим с OpenAI,
    поэтому используется клиент OpenAI с base_url DeepSeek."""

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com",
    ):
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    def _build_messages(self, messages: List[ChatMessage]):
        return [{"role": m.role.value, "content": m.content} for m in messages]

    async def stream(self, messages: List[ChatMessage]) -> AsyncIterator[str]:
        sdk_messages = self._build_messages(messages)

        response = await self._client.chat.completions.create(
            model=self._model, messages=sdk_messages, stream=True
        )

        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    async def complete(self, messages: List[ChatMessage]) -> str:
        sdk_messages = self._build_messages(messages)

        response = await self._client.chat.completions.create(
            model=self._model, messages=sdk_messages
        )

        return response.choices[0].message.content
