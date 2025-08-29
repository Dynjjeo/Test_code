from __future__ import annotations

import dramatiq
from logger import get_logger

from workflows.config import get_config
from workflows.converter.gmail_utils import fetch_mails_in_date, load_allowed_subjects
from workflows.flows.dependencies import embedding_model, os_client, rabbitmq_broker

log = get_logger(__name__)
dramatiq.set_broker(rabbitmq_broker)


@dramatiq.actor
def process_mail_upload():
    """Actor để crawl mail và upload vào OpenSearch."""
    log.info("[UPLOAD] Bắt đầu crawl và upload mail")

    try:
        if not os_client.ping():
            log.error("Không thể kết nối tới OpenSearch!")
            return
        log.info("Kết nối OpenSearch thành công.")
    except Exception as e:
        log.exception(f"Lỗi khi kết nối OS: {e}")
        return

    # Crawl mail và upload trực tiếp vào OpenSearch
    try:
        config = get_config()
        subjects = load_allowed_subjects(
            excel_path=config.tabel_mail, sheet_name=None, keyword=config.col_name
        )

        if not subjects:
            log.warning("Không có allowed subjects nào, dừng crawl")
            return

        fetch_mails_in_date(
            subjects,
            after_default=config.after_mail,
            before_default=config.before_mail,
            os_client=os_client,
            embedding_model=embedding_model,
        )
        log.info("Đã crawl và upload mail vào OpenSearch thành công")

    except Exception as e:
        log.exception(f"Lỗi khi crawl và upload mail: {e}")
        return


# def start_mail_upload():
#     """Khởi động quá trình upload mail."""
#     process_mail_upload.send()
#     log.info("Đã gửi task upload mail vào queue")


# if __name__ == "__main__":
#     process_mail_upload()
