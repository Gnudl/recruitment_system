# Hệ thống quản lý tuyển dụng

Chạy chương trình bằng menu trong terminal. Các lớp dữ liệu nằm trong `models/`,
các thao tác nghiệp vụ và lưu trữ nằm trong `services/`.

## Cách chạy

Mở terminal tại thư mục chứa file `main.py`:

```powershell
python main.py
```

Cũng có thể mở `main.py` trong VS Code và chọn **Run Python File in Terminal**.
Đường dẫn dữ liệu được tính từ vị trí file, không phụ thuộc thư mục terminal.
Chương trình dùng thư viện chuẩn Python; đã kiểm thử với Python 3.14.

Tài khoản mặc định nếu chưa thay đổi:

- Quản trị viên: `admin` / `admin123`.
- Nhân viên: `staff` / `staff123`.

Trong terminal Windows, mật khẩu hiện dấu *; dùng Backspace để sửa và Enter để xác nhận.
Tài khoản mặc định chỉ được tạo khi danh sách tài khoản rỗng.

## Sử dụng menu

- Chọn số tương ứng rồi nhập thông tin theo hướng dẫn.
- Khi sửa, để trống để giữ giá trị hiện tại.
- Ngày phỏng vấn có dạng `YYYY-MM-DD HH:MM`.
- Chỉ nhập `y` khi muốn xác nhận xóa, ghi đè CSV hoặc phục hồi dữ liệu.
- Dữ liệu được lưu tự động sau mỗi thao tác thành công.
- Admin quản lý vị trí, hồ sơ, tài khoản và sao lưu. Staff được xem, tìm kiếm,
  xuất dữ liệu và thao tác phỏng vấn theo kiểm tra quyền trong services.
- Lấy tin tuyển dụng từ API cần kết nối Internet.

Các nhóm chức năng: vị trí tuyển dụng; ứng viên; tìm kiếm và lọc; lịch và kết quả
phỏng vấn; thống kê; xuất CSV; đọc JSON; sao lưu và phục hồi; tài khoản.

## Thư mục

```text
main.py
models/
services/
data/
backups/
tests/
output/       (được tạo khi xuất CSV theo đường dẫn mặc định)
```

Sao lưu nằm tại `backups/`, không phải `data/backups/`.
Phục hồi dùng dữ liệu trước lần ghi đè, có thể mất cập nhật cuối.

## Chạy kiểm thử

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Các bài kiểm thử tự động dùng thư mục tạm. API trong kiểm thử được mô phỏng,
không gọi mạng thực tế.

Các file demo để chụp ảnh báo cáo:

```powershell
python tests/main_recruitment_demo.py
python tests/main_json_demo.py
python tests/main_csv_demo.py
python tests/main_backup_demo.py
```

Demo JSON, CSV và backup lưu kết quả riêng dưới `tests/`.
