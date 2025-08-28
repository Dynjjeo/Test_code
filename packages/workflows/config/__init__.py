from __future__ import annotations

from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

from pydantic import AnyUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

if TYPE_CHECKING:
    from workflows.qa.contanst import ChatbotApiRoutes

# === Singleton config ===
_config: WorkflowsBaseConfig | None = None


def get_config() -> WorkflowsBaseConfig:
    global _config
    if _config is None:
        _config = WorkflowsBaseConfig()
    return _config


# === Main Config Class ===
class WorkflowsBaseConfig(BaseSettings):
    """Cấu hình chính cho hệ thống workflows."""

    model_config = SettingsConfigDict(
        env_prefix="WORKFLOWS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # == API endpoints ==
    chatbot_api_url: AnyUrl
    dotnet_api_url: AnyUrl

    # == Cache folder ==
    cache_dir: Path

    # == RabbitMQ ==
    rabbitmq_url: AnyUrl
    rabbitmq_user: Annotated[str, Field(min_length=3)]
    rabbitmq_password: Annotated[SecretStr, Field(min_length=8)]

    @cached_property
    def rabbitmq_connection_url(self) -> str:
        host = self.rabbitmq_url.host or "chatbot-rabbitmq"
        port = self.rabbitmq_url.port or 5672
        user = self.rabbitmq_user
        password = self.rabbitmq_password.get_secret_value()
        return f"amqp://{user}:{password}@{host}:{port}"

    # == Elasticsearch ==
    elastic_url: AnyUrl
    elastic_user: Annotated[str, Field(min_length=3)]
    elastic_password: Annotated[SecretStr, Field(min_length=8)]

    # == Chunking config ==
    chunk_size: Annotated[int, Field(gt=0)] = 300
    chunk_overlap: Annotated[int, Field(ge=0)] = 50

    # == OpenAI LLM ==
    openai_api_url: AnyUrl
    model_llm_id: Annotated[str, Field(min_length=3)]
    openai_api_key: Annotated[str, Field(min_length=3)]

    # == Local model IDs ==
    model_tokenizer_id: Annotated[str, Field(min_length=3)]
    model_embedding_id: Annotated[str, Field(min_length=3)]
    model_pdf_id: Annotated[str, Field(min_length=3)]

    # == MinIO embedding ==
    minio_endpoint: AnyUrl
    minio_access_key: Annotated[str, Field(min_length=3)]
    minio_secret_key: Annotated[SecretStr, Field(min_length=3)]
    minio_bucket: Annotated[str, Field(min_length=1)]

    ## == Mail ==
    after_mail: Annotated[str, Field(min_length=1)]
    before_mail: Annotated[str, Field(min_length=1)]
    tabel_mail: Path

    @cached_property
    def model_tokenizer_dir(self) -> Path:
        return self.cache_dir / self.model_tokenizer_id

    @cached_property
    def model_pdf_dir(self) -> Path:
        return self.cache_dir / self.model_pdf_id

    @cached_property
    def minio_embedding_path(self) -> str:
        return self.cache_dir / self.model_embedding_id

    @cached_property
    def minio_ollama_path(self) -> str:
        return self.cache_dir / self.model_llm_id

    def route(self, path: ChatbotApiRoutes) -> str:
        return self.chatbot_api_url.unicode_string().rstrip("/") + "/" + path.value
