# Thang Long Da Lat Online Judge

## Giới thiệu

TLOJ - Thang Long Da Lat Online Judge là hệ thống chấm bài tự động của TLOI được xây dựng từ Google Workspace (cụ thể gồm Google Sheets, Forms và Docs) và Google Sheets API. Các bài nộp được chấm bởi phần mềm chấm bài tự động Themis (Lê Minh Hoàng & Đỗ Đức Đông).

## Hệ thống

Hệ thống TLOJ bao gồm:
- [Đăng ký tài khoản](https://tiny.cc/tloj-register)
- [Đề bài](https://tiny.cc/tloj-problems)
- [Nộp bài](https://tiny.cc/tloj-submit)
- [Bảng xếp hạng](https://tiny.cc/tloj-ranking)
- [Lời giải](https://tiny.cc/tloj-solutions)

## Cài đặt

### Cài đặt Themis

Các bạn có thể tải Themis tại [đây](https://dsapblog.wordpress.com/2013/12/24/themis/).

### Cài đặt Python

Các bạn có thể tải Python tại [đây](https://www.python.org/downloads/).

### Cài đặt Google Sheets API

1. Tạo một dự án mới tại [Google Cloud Platform](https://console.cloud.google.com/).
2. Bật Google Sheets API tại [Google API Console](https://console.developers.google.com/).
3. Tạo một Service Account và tải xuống file JSON chứa thông tin xác thực với tên `key.json`.

### Cài đặt các trang cần thiết

Đang cập nhật...

### Cài đặt TLOJ

1. Sao chép repo này về máy:
```bash
git clone https://github.com/kitsunehivern/TLOJ.git
```
2. Cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```
3. Đặt file `key.json` vào thư mục `TLOJ`.
4. Tạo file `data.json` với nội dung tương tự như sau:
```json
{
    "sheet_id": "...",
    
    "problems_data": {
        "A": {
            "name": "...",
            "time_limit": 1
        },
        "B": {
            "name": "...",
            "time_limit": 1
        }
    }
}
```
5. Sửa file `config.py` nếu cần thiết.
6. Chạy chương trình:
```bash
py judge.py
```

## Liên hệ

Mọi ý kiến và đóng góp xin được gửi về:
- TLOI ([fanpage](https://www.facebook.com/tloi.dalat))
- Đinh Cao Minh Quân ([facebook](https://www.facebook.com/kitsunehivern))
- Hoàng Đức Huy ([facebook](https://www.facebook.com/profile.php?id=100017551147817))