import os
import json
import re
import time
from datetime import datetime, timedelta
from simplegmail import Gmail
from simplegmail.query import construct_query

gmail = Gmail()

# Tạo thư mục outputs nếu chưa tồn tại
os.makedirs("outputs", exist_ok=True)

def fetch_and_mark_read():
    # Lấy thời điểm 1 giờ trước
    # one_hour_ago = datetime.utcnow() - timedelta(hours=1)

    # Query lấy mail chưa đọc trong 1 giờ qua, theo labels chỉ định
    query_params = {
        # "newer_than": (1, "hour"),
        # "unread": True,
        "labels": ["SENT"], 
        "after": "2024/05/22", 
        # "before": "2025/07/14"
    }
    query = construct_query(query_params)

    # Lấy danh sách email
    messages = gmail.get_messages(query=query)
    print(f"[{datetime.now()}] Tìm thấy {len(messages)} email mới.")

    for i, message in enumerate(messages, start=1):
        mail_data = {
            "id": message.id,
            "thread_id": message.thread_id,
            # "headers": message.headers,
            "from": message.sender,
            "to": message.recipient,
            "subject": message.subject,
            "date": str(message.date),
            "snippet": message.snippet,
            "plain_text": message.plain,
            "cc": message.cc,
            "bcc": message.bcc,
            "labels_ids": [label.name for label in message.label_ids],
            "attachments": [att.filename for att in message.attachments]
        }

        # Tên file an toàn
        safe_subject = re.sub(r'[\\/*?:"<>|]', "_", message.subject or "no_subject")
        filename = os.path.join("outputs", f"email_{i}_{safe_subject}.json")

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(mail_data, f, ensure_ascii=False, indent=4)

        print(f"Đã lưu: {filename}")

        # Đánh dấu đã đọc
        message.mark_as_read()

while True:
    fetch_and_mark_read()
    print("Đợi 1 phút...")
    time.sleep(60) 
