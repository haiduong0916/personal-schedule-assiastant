🛠 Yêu cầu hệ thống & Cài đặt
Yêu cầu
Python 3.x trở lên.
Hệ điều hành: Windows (Khuyến nghị để hỗ trợ tốt âm thanh winsound).
Cài đặt thư viện
Dự án sử dụng một số thư viện ngoài để xử lý thời gian và ngôn ngữ. Bạn cần cài đặt chúng trước khi chạy:
pip install dateparser underthesea unidecode
(Lưu ý: Các thư viện tkinter, sqlite3, calendar thường đã có sẵn trong bộ cài Python chuẩn).
🚀 Hướng dẫn sử dụng
Khởi chạy ứng dụng:
Mở terminal tại thư mục dự án và chạy lệnh:
python main.py


Thêm sự kiện:
Nhập câu lệnh vào ô trống. Ví dụ:
Họp team lúc 9h sáng mai
Di choi voi ny luc 19h30 toi nay o rap CGV
Nộp báo cáo deadline 12/12
Đá bóng sân K3 lúc 5h chiều nhắc trước 30p
Nhấn Enter hoặc nút Thêm Sự Kiện.
Xem & Quản lý:
Chọn "Dạng Lịch" để xem tổng quan tháng.
Chọn "Dạng Danh Sách" để xem chi tiết và thực hiện Sửa/Xóa.
Sử dụng thanh Tìm kiếm để lọc nhanh sự kiện.
Sửa sự kiện:
Chọn sự kiện trong danh sách -> Nhấn Sửa.
Bạn có thể nhập lại thời gian theo ngôn ngữ tự nhiên (VD: sửa thành "chiều mai") hoặc định dạng chuẩn.
📂 Cấu trúc thư mục
personal-schedule-assistant/
│
├── main.py           # File chính: Chứa giao diện (GUI) và logic điều khiển
├── nlp_engine.py     # Module xử lý ngôn ngữ tự nhiên và logic thời gian
├── database.py       # Module quản lý cơ sở dữ liệu SQLite
├── schedule.db       # File cơ sở dữ liệu (Tự động tạo khi chạy lần đầu)
└── README.md         # Tài liệu hướng dẫn


🧠 Giải pháp NLP (Chi tiết kỹ thuật)
Module NLP Engine hoạt động theo mô hình Hybrid (Lai) qua 5 bước:
Tiền xử lý: Chuẩn hóa văn bản về chữ thường, xử lý các từ viết tắt (trc -> trước, t2 -> thứ 2).
Trích xuất Thời gian (Time Extraction):
Ưu tiên bắt các ngày tháng cụ thể (dd/mm) bằng Regex.
Sử dụng thư viện dateparser cho các cụm từ tương đối (mai, mốt).
Kiểm tra tính hợp lệ (Validation) để loại bỏ ngày sai (30/2) hoặc quá khứ.
Trích xuất Địa điểm (Location Extraction): Dựa trên từ khóa chỉ báo (tại, ở, phòng, sân...) và thuật toán cắt chuỗi thông minh.
Xác định Hành động (Event Name): Sử dụng từ điển động từ (đi, họp, làm...) để xác định nội dung chính và loại bỏ các từ rác (nhắc tôi, vào lúc...).
Hợp nhất: Đóng gói kết quả thành cấu trúc dữ liệu chuẩn để lưu vào Database.
