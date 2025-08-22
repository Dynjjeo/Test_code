# LƯU Ý:
- Các file như: allowed_subjects.xlsx, client_secret.json, gmail_token.json là các mail minh họa
- Nếu muốn crawl đúng mail và đúng các trường thì thực hiện theo các bước ở foler Hướng dẫn và thay đổi tên file và tên trường trong file `simple_gmail.py`
    - Có thể sử đổi khoảng thời gian lấy:  ở dòng 116 có biến "after"
    - Ở dòng 45 và 49 thay đỏi từ "subject" thành tên trường mà lưu trữ trường giá trị subject
    - Ở dòng 184 thì thay đổi tên file xlsx chứa trường subject
- Sau đó thực hiện các bước cài đặt môi trường và chạy python `simple_gmail.py`
  
