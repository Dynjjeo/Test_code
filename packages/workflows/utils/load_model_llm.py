from __future__ import annotations

from pathlib import Path

import boto3
from workflows.config import get_config

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None


def download_model_from_minio_if_needed(model_id: str) -> Path:
    """Tải model từ MinIO về cache nếu chưa tồn tại.
    Trả về đường dẫn local chứa model.
    """  # noqa: D205, DOC501
    config = get_config()
    cache_dir = Path(config.cache_dir).expanduser()
    local_path = cache_dir / model_id

    # Nếu đã tồn tại và có file
    if local_path.exists() and any(local_path.glob("*")):
        print(f" Model `{model_id}` đã tồn tại ở `{local_path}`. Bỏ qua tải lại.")
        return local_path

    print(f"  Đang tải model `{model_id}` từ MinIO...")

    client = boto3.client(
        "s3",
        endpoint_url=str(config.minio_endpoint),
        aws_access_key_id=config.minio_access_key,
        aws_secret_access_key=config.minio_secret_key.get_secret_value(),
    )

    prefix = model_id.strip("/")
    paginator = client.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=config.minio_bucket, Prefix=prefix)

    found = False
    for page in pages:
        for obj in page.get("Contents", []):
            found = True
            key = obj["Key"]
            relative_path = Path(key).relative_to(prefix)
            file_path = local_path / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            client.download_file(config.minio_bucket, key, str(file_path))

    if not found:
        msg = f"Không tìm thấy model `{model_id}` trong bucket `{config.minio_bucket}` với prefix `{prefix}`"
        raise FileNotFoundError(msg)

    print(f" Đã tải model `{model_id}` về `{local_path}`")
    return local_path


def load_model_llm(model_id: str, **kwargs):
    local_dir = download_model_from_minio_if_needed(model_id)

    # Trường hợp: Ollama / llama.cpp (.bin)
    bin_files = list(Path(local_dir).rglob("*.bin"))
    if bin_files and Llama is not None:
        model_file = bin_files[0]
        print(f" Đang load LLaMA model từ {model_file}")
        return Llama(model_path=str(model_file), **kwargs)
    return None


def load_atta_file(atta_file_id: str) -> Path:
    local_dir = download_model_from_minio_if_needed(atta_file_id)
    return local_dir


# === Test nhanh ===
if __name__ == "__main__":
    # Ví dụ: tải model ollama từ MinIO
    model_id = "ollama"  # Thư mục chứa file .bin trên MinIO
    llm = load_model_llm(
        model_id,
        n_ctx=2048,
        n_threads=8,
        verbose=False,
    )
    # llama_cpp model
    output = llm("Tôi đang đi làm", max_tokens=50)
    print(output["choices"][0]["text"])
