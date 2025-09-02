from __future__ import annotations

from typing import Any

from logger.src.logger import get_logger
from opensearchpy import OpenSearch  # type: ignore

log = get_logger(__name__)

# Mapping cho email index
EMAIL_INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "embedding": {
                "type": "dense_vector",
                "dims": 1536,  # Dimension cho OpenAI embedding
                "index": True,
                "similarity": "cosine"
            },
            "metadata": {
                "properties": {
                    "thread_id": {"type": "keyword"},
                    "from": {"type": "keyword"},
                    "to": {"type": "keyword"},
                    "subject": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "date": {"type": "date"},
                    "labels_ids": {"type": "keyword"},
                    "attachments": {
                        "type": "nested",
                        "properties": {
                            "filename": {"type": "keyword"},
                            "content": {
                                "type": "text",
                                "analyzer": "standard"
                            }
                        }
                    }
                }
            }
        }
    },
    "settings": {
        "index": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "refresh_interval": "1s"
        }
    }
}


# ----------------- Client -----------------
def new_os_client(url: str, user: str, password: str) -> OpenSearch:
    """Tạo OpenSearch client với cấu hình tối ưu."""
    try:
        os_client = OpenSearch(
            hosts=[url],
            http_auth=(user, password),
            use_ssl=True,
            verify_certs=False,
            ssl_show_warn=False,
            timeout=30,
            max_retries=5,
            retry_on_timeout=True,
            connection_class=None,
        )
        log.info("os_service.new_os_client.success", url=url)
        return os_client
    except Exception as e:
        log.error("os_service.new_os_client.error", url=url, error=str(e))
        raise


def ping_opensearch(os_client: OpenSearch) -> bool:
    """Ping OpenSearch để kiểm tra kết nối"""
    try:
        is_alive = os_client.ping()
        log.info("os_service.ping", status=is_alive)
        return is_alive
    except Exception as e:
        log.error("os_service.ping.error", error=str(e))
        return False


# ----------------- Index Management -----------------
def create_index(
    os_client: OpenSearch, index: str, mapping: dict[str, Any] | None = None
) -> dict[str, Any] | None:
    """Tạo index nếu chưa tồn tại."""
    try:
        if os_client.indices.exists(index=index):
            log.info("os_service.create_index.exists", index=index)
            return None

        # Sử dụng email mapping mặc định nếu không có mapping
        if mapping is None:
            mapping = EMAIL_INDEX_MAPPING

        response = os_client.indices.create(index=index, body=mapping)
        log.info("os_service.create_index.success", index=index)
        return response

    except Exception as e:
        log.error("os_service.create_index.error", index=index, error=str(e))
        raise


def delete_index(os_client: OpenSearch, index: str) -> dict[str, Any] | None:
    """Xóa index."""
    try:
        if not os_client.indices.exists(index=index):
            log.info("os_service.delete_index.not_exists", index=index)
            return None

        response = os_client.indices.delete(index=index)
        log.info("os_service.delete_index.success", index=index)
        return response

    except Exception as e:
        log.error("os_service.delete_index.error", index=index, error=str(e))
        raise


def get_index_info(os_client: OpenSearch, index: str) -> dict[str, Any] | None:
    """Lấy thông tin về index."""
    try:
        if not os_client.indices.exists(index=index):
            log.info("os_service.get_index_info.not_exists", index=index)
            return None

        response = os_client.indices.get(index=index)
        log.info("os_service.get_index_info.success", index=index)
        return response

    except Exception as e:
        log.error("os_service.get_index_info.error", index=index, error=str(e))
        return None


# ----------------- Document Operations -----------------
def upload_document(
    os_client: OpenSearch, index: str, doc_id: str, payload: dict[str, Any]
) -> dict[str, Any] | None:
    """Upload hoặc update một document vào OpenSearch."""
    try:
        response = os_client.index(
            index=index,
            id=doc_id,
            document=payload,  # Sử dụng document thay vì body
            refresh=True
        )
        log.info("os_service.upload_document.success", index=index, doc_id=doc_id)
        return response

    except Exception as e:
        log.error("os_service.upload_document.error", index=index, doc_id=doc_id, error=str(e))
        return None


def get_document(
    os_client: OpenSearch, index: str, doc_id: str
) -> dict[str, Any] | None:
    """Lấy document theo ID."""
    try:
        response = os_client.get(index=index, id=doc_id)
        log.info("os_service.get_document.success", index=index, doc_id=doc_id)
        return response

    except Exception as e:
        log.error("os_service.get_document.error", index=index, doc_id=doc_id, error=str(e))
        return None


def document_exists(os_client: OpenSearch, index: str, doc_id: str) -> bool:
    """Kiểm tra document có tồn tại không."""
    try:
        exists = os_client.exists(index=index, id=doc_id)
        log.info("os_service.document_exists", index=index, doc_id=doc_id, exists=exists)
        return exists

    except Exception as e:
        log.error("os_service.document_exists.error", index=index, doc_id=doc_id, error=str(e))
        return False


def delete_document(os_client: OpenSearch, index: str, doc_id: str) -> dict[str, Any] | None:
    """Xóa một document theo doc_id."""
    try:
        if not document_exists(os_client, index, doc_id):
            log.info("os_service.delete_document.not_exists", index=index, doc_id=doc_id)
            return None

        response = os_client.delete(index=index, id=doc_id, refresh=True)
        log.info("os_service.delete_document.success", index=index, doc_id=doc_id)
        return response

    except Exception as e:
        log.error("os_service.delete_document.error", index=index, doc_id=doc_id, error=str(e))
        return None


def bulk_upload_documents(
    os_client: OpenSearch,
    index: str,
    documents: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Upload nhiều documents cùng lúc để tăng performance."""
    try:
        from opensearchpy.helpers import bulk

        actions = []
        for doc in documents:
            action = {
                "_index": index,
                "_id": doc["id"],
                "_source": {
                    "embedding": doc["embedding"],
                    "metadata": doc["metadata"]
                }
            }
            actions.append(action)

        response = bulk(os_client, actions, refresh=True)
        log.info("os_service.bulk_upload.success", index=index, count=len(documents))
        return response

    except Exception as e:
        log.error("os_service.bulk_upload.error", index=index, error=str(e))
        return None


# ----------------- Search Operations -----------------
def search_documents(
    os_client: OpenSearch,
    index: str,
    query: dict[str, Any],
    size: int = 10
) -> dict[str, Any] | None:
    """Tìm kiếm documents."""
    try:
        response = os_client.search(
            index=index,
            body=query,
            size=size
        )
        log.info("os_service.search_documents.success", index=index, hits=response["hits"]["total"]["value"])
        return response

    except Exception as e:
        log.error("os_service.search_documents.error", index=index, error=str(e))
        return None


def vector_search(
    os_client: OpenSearch,
    index: str,
    query_vector: list[float],
    size: int = 10,
    min_score: float = 0.0
) -> dict[str, Any] | None:
    """Tìm kiếm vector similarity."""
    try:
        query = {
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_vector,
                        "k": size
                    }
                }
            },
            "min_score": min_score
        }

        response = os_client.search(
            index=index,
            body=query,
            size=size
        )
        log.info("os_service.vector_search.success", index=index, hits=response["hits"]["total"]["value"])
        return response

    except Exception as e:
        log.error("os_service.vector_search.error", index=index, error=str(e))
        return None


# ----------------- Index Stats -----------------
def get_index_stats(os_client: OpenSearch, index: str) -> dict[str, Any] | None:
    """Lấy thống kê index."""
    try:
        response = os_client.indices.stats(index=index)
        log.info("os_service.get_index_stats.success", index=index)
        return response

    except Exception as e:
        log.error("os_service.get_index_stats.error", index=index, error=str(e))
        return None


def count_documents(os_client: OpenSearch, index: str) -> int:
    """Đếm số documents trong index."""
    try:
        response = os_client.count(index=index)
        count = response["count"]
        log.info("os_service.count_documents.success", index=index, count=count)
        return count

    except Exception as e:
        log.error("os_service.count_documents.error", index=index, error=str(e))
        return 0


# ----------------- Utility Functions -----------------
def refresh_index(os_client: OpenSearch, index: str) -> dict[str, Any] | None:
    """Force refresh index để có thể search ngay."""
    try:
        response = os_client.indices.refresh(index=index)
        log.info("os_service.refresh_index.success", index=index)
        return response

    except Exception as e:
        log.error("os_service.refresh_index.error", index=index, error=str(e))
        return None