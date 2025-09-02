import base64
import logging
import os
import warnings

import pandas as pd
from bs4 import XMLParsedAsHTMLWarning
from google.auth.transport.requests import Request  # noqa: E402
from google.oauth2.credentials import Credentials  # noqa: E402
from google_auth_oauthlib.flow import InstalledAppFlow  # noqa: E402
from googleapiclient.discovery import build  # noqa: E402
from simplegmail.query import construct_query
from docling_core.types.doc import ImageRefMode, PictureItem, TableItem
from libs.vectordb.src.vectordb.opensearch import os_service
from workflows.config import get_config

# Import docling để đọc tệp đính kèm
try:
    # from docling.datamodel.base_models import InputFormat
    from docling.document_converter import DocumentConverter

    DOCLING_AVAILABLE = True
    logging.info("Docling đã được import thành công")
except ImportError:
    DOCLING_AVAILABLE = False
    logging.warning("Docling không có sẵn. Cần cài đặt: pip install docling")

# Ẩn cảnh báo BeautifulSoup XMLParsedAsHTMLWarning
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Cấu hình logging -> ghi log ra file
logging.basicConfig(
    filename="mail_fetcher.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

INDEX_NAME = "emails"
downloaded_ids = set()

# Các định dạng file được hỗ trợ bởi docling
SUPPORTED_FORMATS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".xlsx",
    ".html",
    ".md",
    ".txt",
    ".doc",
    ".ppt",
    ".xls",
    ".rtf",
    ".odt",
    ".odp",
    ".ods",
}

CREDENTIALS_FILE = os.getenv("WORKFLOWS_CLIENT_SECRET")
TOKEN_FILE = os.getenv("WORKFLOWS_GMAIL_TOKEN")


def init_gmail_service():
    SCOPES = [
        "https://www.googleapis.com/auth/gmail.settings.basic",
        "https://www.googleapis.com/auth/gmail.modify",
    ]

    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # nếu chưa có gmail_token thì thực hiện
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    # build gmail service
    service = build("gmail", "v1", credentials=creds)
    return service


def normalize_subject(subject: str) -> str:
    """
    Chuẩn hóa subject: loại bỏ khoảng trắng thừa ở đầu và cuối.
    """
    if not subject:
        return ""
    return subject.strip()


def load_allowed_subjects(
    excel_path: str, sheet_name: str = None, keyword: str = "subject"
) -> list:
    """
    Đọc danh sách subject từ file Excel.
    - Tự động tìm cột chứa keyword.
    - Bỏ các cột Unnamed.
    """
    if not os.path.exists(excel_path):
        logging.error(f"Không tìm thấy file {excel_path}")
        return []

    # 1. Đọc toàn bộ sheet mà không lấy header
    df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)

    # 2. Tìm dòng header thực sự (dòng có keyword)
    header_row_idx = None
    for i, row in df.iterrows():
        # tìm keyword trong row (bỏ qua NaN)
        if any(
            isinstance(cell, str) and keyword.lower() in cell.lower()
            for cell in row
            if cell
        ):
            header_row_idx = i
            break
    if header_row_idx is None:
        logging.error(
            f"Không tìm thấy cột chứa từ khóa '{keyword}' trong file {excel_path}"
        )
        return []

    # 3. Đọc lại sheet với header đúng
    df_table = pd.read_excel(excel_path, sheet_name=sheet_name, header=header_row_idx)

    # 4. Loại bỏ các cột Unnamed
    df_table = df_table.loc[:, ~df_table.columns.str.contains("^Unnamed")]

    # 5. Tìm cột chứa keyword
    matched_cols = [
        col for col in df_table.columns if keyword.lower() in str(col).lower()
    ]
    if not matched_cols:
        logging.error(f"Không tìm thấy cột chứa từ khóa '{keyword}' sau khi đọc bảng.")
        return []

    # 6. Lấy dữ liệu từ cột đầu tiên match keyword
    col_name = matched_cols[0]
    subjects = (
        df_table[col_name].dropna().apply(lambda x: normalize_subject(str(x))).tolist()
    )

    logging.info(f"Đã load {len(subjects)} ALLOWED_SUBJECTS từ {excel_path}")
    return subjects


def extract_content_with_docling(file_data, filename):
    """
    Sử dụng docling để trích xuất nội dung từ file data (không lưu file)
    """
    if not DOCLING_AVAILABLE:
        logging.warning("Docling không có sẵn, không thể trích xuất nội dung")
        return None

    try:
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in SUPPORTED_FORMATS:
            logging.info(f"File {filename} có định dạng không được hỗ trợ: {file_ext}")
            return None

        # Tạo file tạm để docling xử lý
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as temp_file:
            temp_file.write(file_data)
            temp_path = temp_file.name

        try:
            converter = DocumentConverter()
            result = converter.convert(temp_path)
            doc_file = result.input.file.stem

            for page_no, page in result.document.pages.items():
                page_no = page.page_no
                page_image_filename = f"{doc_file}_page_{page_no}.png"
                with page_image_filename.open("wb") as img_f:
                    img_f.write(page.image)
            table_counter = 0
            picture_counter = 0
            for element, _level in result.document.iterate_elements():
                if isinstance(element, TableItem):
                    table_counter += 1
                    # element.image_ref = ImageRefMode.FILE
                    element_image_filename = f"{doc_file}_table_{table_counter}.png"
                    with element_image_filename.open("wb") as img_f:
                        element.get_image(result.document).save(img_f, format="PNG")
                if isinstance(element, PictureItem):
                    picture_counter += 1
                    # element.image_ref = ImageRefMode.FILE
                    element_image_filename = f"{doc_file}_picture_{picture_counter}.png"
                    with element_image_filename.open("wb") as img_f:
                        element.get_image(result.document).save(img_f, format="PNG")
            # Lưu file md với embedding hình ảnh
            md_filename = f"{doc_file}_with_img.md"
            result.document.save_as_markdown(
                md_filename, image_ref_mode=ImageRefMode.EMBEDDED            )
            # Đọc nội dung md với hình ảnh được tham chiếu bến ngoài
            md_filename = f"{doc_file}_with_img_refs.md"
            result.document.save_as_markdown(
                md_filename, image_ref_mode=ImageRefMode.REFERENCE         )
            return result.document.export_to_markdown()
        finally:
            os.unlink(temp_path)  # Xóa file tạm

    except Exception as e:
        logging.error(f"Lỗi khi trích xuất nội dung từ {filename}: {e}")
        return None


def process_attachments(service, user_id, msg_id):
    """Lấy và xử lý tất cả tệp đính kèm của 1 email."""
    attachments_info = []

    try:
        message = service.users().messages().get(userId=user_id, id=msg_id).execute()
        payload = message.get("payload", {})

        def _extract_parts(parts):
            for part in parts:
                if part.get("filename"):
                    body = part.get("body", {})
                    att_id = body.get("attachmentId")
                    if att_id:
                        att = (
                            service.users()
                            .messages()
                            .attachments()
                            .get(userId=user_id, messageId=msg_id, id=att_id)
                            .execute()
                        )
                        data = att.get("data")
                        if data:
                            file_data = base64.urlsafe_b64decode(data.encode("UTF-8"))
                            attachment_context = extract_content_with_docling(
                                file_data, part["filename"]
                            )

                            attachment_info = {
                                "filename": part["filename"],
                                "content": attachment_context
                                if attachment_context
                                else None,
                            }
                            attachments_info.append(attachment_info)

                if "parts" in part:
                    _extract_parts(part["parts"])

        if "parts" in payload:
            _extract_parts(payload["parts"])

    except Exception as e:
        logging.error(f"Lỗi xử lý file đính kèm từ mail {msg_id}: {e}")

    return attachments_info


def save_mail_to_opensearch(mail_data, os_client, embedding_model):
    """Lưu một email vào OpenSearch với mail_id làm document ID."""
    try:
        mail_id = mail_data["id"]
        plain_text = mail_data.get("plain_text") or ""

        # Tạo vector embedding từ plain_text
        embedding = embedding_model.get_text_embedding(plain_text)

        # Chuẩn bị metadata (chỉ các trường yêu cầu)
        metadata = {
            "thread_id": mail_data["thread_id"],
            "from": mail_data.get("from"),
            "to": mail_data.get("to"),
            "subject": mail_data.get("subject"),
            "date": mail_data.get("date"),
            "plain_text": plain_text,
            "labels_ids": mail_data.get("labels_ids", []),
            "attachments": mail_data.get("attachments", []),
        }

        doc = {
            "embedding": embedding,
            "metadata": metadata,
        }

        # Upload vào OpenSearch với mail_id làm document ID
        result = os_service.upload_document(
            os_client=os_client,
            index=INDEX_NAME,
            doc_id=mail_id,
            payload=doc,
        )

        if result:
            logging.info(f"Đã upload mail {mail_id} vào OpenSearch")
        else:
            logging.error(f"Không thể upload mail {mail_id} vào OpenSearch")

    except Exception as e:
        logging.error(f"Lỗi khi upload mail {mail_data.get('id')} vào OpenSearch: {e}")


def fetch_mails_in_date(
    allowed_subjects, after_default, before_default, os_client, embedding_model
):
    """Crawl emails và upload trực tiếp vào OpenSearch."""

    # Đảm bảo index emails tồn tại
    try:
        os_service.create_index(os_client, INDEX_NAME)
    except Exception as e:
        logging.error(f"Lỗi khi tạo index: {e}")
        return

    query_params = {
        "after": after_default,
        "before": before_default,
    }
    query = construct_query(query_params)
    gmail = init_gmail_service()

    try:
        messages = gmail.get_messages(query=query)
        logging.info(f"Tìm thấy {len(messages)} email.")
    except Exception as e:
        logging.error(f"Lỗi khi fetch mail: {e}")
        return

    # Gom thread_id -> danh sách mail
    threads = {}
    valid_threads = set()

    for msg in messages:
        if msg.id in downloaded_ids:
            continue

        subj_norm = normalize_subject(msg.subject)

        # Nếu subject khớp danh sách allowed -> thread này được chấp nhận
        if subj_norm in allowed_subjects:
            valid_threads.add(msg.thread_id)

        threads.setdefault(msg.thread_id, []).append(msg)
        downloaded_ids.add(msg.id)

    # Xử lý từng email và upload vào OpenSearch
    total_uploaded = 0
    for thread_id, msgs in threads.items():
        if thread_id not in valid_threads:
            continue

        msgs_sorted = sorted(msgs, key=lambda x: x.date)

        for msg in msgs_sorted:
            # Xử lý attachments (không lưu file)
            attachments_info = []
            if msg.attachments:
                attachments_info = process_attachments(gmail.service, "me", msg.id)

            # Chuẩn bị dữ liệu mail
            mail_data = {
                "id": msg.id,
                "thread_id": thread_id,
                "from": msg.sender,
                "to": msg.recipient,
                "subject": msg.subject,
                "date": str(msg.date),
                "plain_text": msg.plain,
                "labels_ids": [label.name for label in msg.label_ids],
                "attachments": attachments_info,
            }

            # Upload trực tiếp vào OpenSearch với mail_id làm document ID
            save_mail_to_opensearch(mail_data, os_client, embedding_model)
            total_uploaded += 1

        logging.info(f"Đã xử lý thread {thread_id} với {len(msgs_sorted)} emails")

    logging.info(f"Tổng cộng đã upload {total_uploaded} emails vào OpenSearch")


if __name__ == "__main__":
    config = get_config()
    excel_path = config.tabel_mail
    after_default = config.after_mail
    before_default = config.before_mail
    col_name = config.col_name

    subjects = load_allowed_subjects(
        excel_path=excel_path, sheet_name=None, keyword=col_name
    )
    print(subjects)
    if not subjects:
        print("Không có ALLOWED_SUBJECTS nào, thoát.")
    else:
        # Import dependencies để test
        from workflows.flows.dependencies import embedding_model, os_client

        fetch_mails_in_date(
            subjects, after_default, before_default, os_client, embedding_model
        )
