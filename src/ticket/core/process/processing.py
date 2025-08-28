import os
import re

import boto3
from dotenv import load_dotenv

load_dotenv()


def load_stopwords_from_minio(file_path: str) -> set[str]:
    """
    Load stopwords từ file trên MinIO
    """
    endpoint = os.getenv("TICKET_OPENAI_API_URL")
    access_key = os.getenv("TICKET_MINIO_ACCESS_KEY")
    secret_key = os.getenv("TICKET_MINIO_SECRET_KEY")
    bucket_name = os.getenv("TICKET_MINIO_BUCKET")

    if not all([endpoint, access_key, secret_key, bucket_name, file_path]):
        print("Thiếu thông tin MinIO hoặc file_path rỗng.")
        return set()

    try:
        client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        response = client.get_object(Bucket=bucket_name, Key=file_path)
        content = response["Body"].read().decode("utf-8")
        return {line.strip().lower() for line in content.splitlines() if line.strip()}
    except Exception as e:
        print(f"Không thể tải stopwords từ MinIO: {file_path} - {e}")
        return set()


# Load stopwords từ MinIO (tiếng Việt, tiếng Anh)
STOPWORDS_VI_PATH = os.getenv("STOPWORDS_VIE")
STOPWORDS_EN_PATH = os.getenv("STOPWORDS_EN")
STOPWORDS_VI = load_stopwords_from_minio(STOPWORDS_VI_PATH)
STOPWORDS_EN = load_stopwords_from_minio(STOPWORDS_EN_PATH)
STOPWORDS_ALL = STOPWORDS_VI | STOPWORDS_EN

# Regex bắt emoji
EMOJI_PATTERN = re.compile(
    "["
    "\U0001f600-\U0001f64f"  # emoticons
    "\U0001f300-\U0001f5ff"  # symbols & pictographs
    "\U0001f680-\U0001f6ff"  # transport & map symbols
    "\U0001f1e0-\U0001f1ff"  # flags
    "]+",
    flags=re.UNICODE,
)


def clean_text(raw_text: str, use_lang: str = "all") -> str:
    """
    1. Xóa HTML tags
    2. Xóa emoji
    3. Xóa stopwords (từ MinIO)
       - use_lang = "vi"  -> chỉ dùng stopwords tiếng Việt
       - use_lang = "en"  -> chỉ dùng stopwords tiếng Anh
       - use_lang = "all" -> cả 2
    """
    # Xóa HTML tag
    text = re.sub(re.compile("<.*?>"), "", raw_text)

    # Xóa emoji
    text = EMOJI_PATTERN.sub(r"", text)

    # Chọn stopwords theo ngôn ngữ
    if use_lang == "vi":
        stop_words = STOPWORDS_VI
    elif use_lang == "en":
        stop_words = STOPWORDS_EN
    else:
        stop_words = STOPWORDS_ALL

    # Tokenize và lọc stopwords
    tokens = re.findall(r"\b\w+\b", text.lower())
    filtered_tokens = [w for w in tokens if w not in stop_words]

    return " ".join(filtered_tokens)


sample = "<p>Hello 😃, đây là ví dụ để test stopwords!</p>"
print(clean_text(sample, use_lang="all"))
