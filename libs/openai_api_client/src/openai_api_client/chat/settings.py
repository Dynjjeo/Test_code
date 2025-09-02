from __future__ import annotations

from typing import TypedDict


class ChatModelSettings(TypedDict, total=False):
    max_tokens: int
    temperature: float
    top_p: float
    presence_penalty: float
    frequency_penalty: float
