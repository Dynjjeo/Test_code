import os
import sys

# Lấy thư mục gốc của project (Test_code)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
# Thêm thư mục packages (nơi chứa workflows)
PACKAGES_DIR = os.path.join(ROOT_DIR, "packages")
sys.path.insert(0, PACKAGES_DIR)

from workflows.config import get_config  # noqa: E402
from workflows.converter.gmail_utils import (  # noqa: E402
    fetch_mails_in_date,
    load_allowed_subjects,
)
from workflows.flows.dependencies import (  # noqa: E402
    embedding_model,
    os_client,
)


def test_gmail_utils():
    """Test chạy gmail_utils trực tiếp"""
    try:
        print("Đang load config...")
        config = get_config()

        print(" Đang load allowed subjects từ Excel...")
        subjects = load_allowed_subjects(
            excel_path=config.tabel_mail, sheet_name=None, col_name=config.col_name
        )

        print(f" Load được {len(subjects)} subjects: {subjects[:5]}...")  # Show 5 đầu

        if not subjects:
            print("Không có ALLOWED_SUBJECTS nào, thoát.")
            return

        print("Đang test kết nối OpenSearch...")
        if not os_client.ping():
            print("Không kết nối được OpenSearch!")
            return
        print(" OpenSearch OK")

        print("Bắt đầu crawl và upload mail...")
        fetch_mails_in_date(
            subjects, config.after_mail, config.before_mail, os_client, embedding_model
        )

        print(" Hoàn thành!")

    except ImportError as e:
        print(f"Import error: {e}")
        print("Đảm bảo đã cài đặt tất cả dependencies")
    except Exception as e:
        print(f"Lỗi: {e}")


if __name__ == "__main__":
    test_gmail_utils()
