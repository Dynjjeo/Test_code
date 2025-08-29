from __future__ import annotations

from typing import TYPE_CHECKING

import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from openai_api_client.embedding import EmbeddingModel
from opensearchpy import OpenSearch

from libs.vectordb.src.vectordb.opensearch import os_service
from workflows.config import get_config

if TYPE_CHECKING:
    pass


def get_rabbitmq_broker() -> RabbitmqBroker:
    """Khởi tạo và trả về RabbitMQ broker để Dramatiq dùng làm message queue.

    - Kết nối tới RabbitMQ dựa vào URL từ config.
    - Đăng ký broker cho Dramatiq (`dramatiq.set_broker`).

    Returns:
        RabbitmqBroker: Kết nối tới RabbitMQ.
    """
    config = get_config()
    broker = RabbitmqBroker(url=config.rabbitmq_connection_url)
    dramatiq.set_broker(broker)
    return broker


def get_os_client() -> OpenSearch:
    """Khởi tạo client kết nối tới Opensearch.

    - Sử dụng URL, user, password từ config.
    - Client này được dùng để lưu và tìm kiếm dữ liệu (vector + metadata).

    Returns:
        Opensearch: Client kết nối ES.
    """
    config = get_config()
    return os_service.new_os_client(
        config.open_url.unicode_string(),
        config.open_user,
        config.open_password.get_secret_value(),
    )


def get_embedding_model() -> EmbeddingModel:
    """Khởi tạo model sinh embedding từ OpenAI API
    - Lấy API URL và model_id từ config
    - Dùng để convert text thành vector embedding lưu vào OS
    Returns:
        EmbeddingModel: Model_embedding
    """
    config = get_config()
    return EmbeddingModel(model_embedding_id=config.model_embedding_id)


## ===============Khởi tạo các đối tượng toàn cục ======
config = get_config()
rabbitmq_broker = get_rabbitmq_broker()  # kết nối RabbitMQ
os_client = get_os_client()  # Kết nối Opensearch
embedding_model = get_embedding_model()  # Model embedding
