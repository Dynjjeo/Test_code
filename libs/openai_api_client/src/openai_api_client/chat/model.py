from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from openai import NOT_GIVEN, OpenAI
from pydantic import BaseModel


if TYPE_CHECKING:
    from collections.abc import Iterable

    from openai_api_client.types import ChatCompletionMessageParam
    from openai_api_client.chat.settings import ChatModelSettings


class ChatUserMessage(BaseModel):
    role: Literal["user"]
    content: str


class ChatModel:
    def __init__(self, openai_api_url: str, openai_api_key: str, model_id: str) -> None:
        self.model_id = model_id

        self.client = OpenAI(base_url=openai_api_url, api_key=openai_api_key)

    def execute(
        self,
        messages: Iterable[ChatCompletionMessageParam],
        settings: ChatModelSettings | None,
    ) -> str | None:
        settings = settings or {}

        results = self.client.chat.completions.create(
            messages=messages,
            model=self.model_id,
            stream=False,
            # model settings
            max_tokens=settings.get("max_tokens", NOT_GIVEN),
            temperature=settings.get("temperature", NOT_GIVEN),
            top_p=settings.get("top_p", NOT_GIVEN),
            presence_penalty=settings.get("presence_penalty", NOT_GIVEN),
            frequency_penalty=settings.get("frequency_penalty", NOT_GIVEN),
        )
        return results.choices[0].message.content
