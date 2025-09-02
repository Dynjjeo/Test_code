from __future__ import annotations

from typing import TYPE_CHECKING

from openai import OpenAI


if TYPE_CHECKING:
    from collections.abc import Iterable


class EmbeddingModel:
    def __init__(self, openai_api_url: str, openai_api_key: str, model_id: str) -> None:
        self.model_id = model_id

        self.client = OpenAI(base_url=openai_api_url, api_key=openai_api_key)

    def embed(self, item: str) -> list[float]:
        """Embed a single text string, return a list of floats."""
        return next(iter(self.embed_multi([item])))

    def embed_multi(self, items: list[str]) -> Iterable[list[float]]:
        """Embed a batch of strings, return a lists of lists of floats."""
        results = self.client.embeddings.create(
            model=self.model_id,
            input=items,
        ).data
        return ([float(r) for r in result.embedding] for result in results)
