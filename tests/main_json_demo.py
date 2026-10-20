from pathlib import Path
import sys

# File chạy thử được đặt trong thư mục tests.
project_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_dir))

from services.file_manager import FileManager


def main():
    # Lưu dữ liệu thử riêng để giữ nguyên dữ liệu chính.
    demo_dir = project_dir / "tests" / "demo_json"
    file_manager = FileManager(demo_dir)
    filename = "candidates_sample.json"

    data = [
        {
            "person_id": "C01",
            "full_name": "Nguyễn Văn An",
            "email": "an@example.com",
            "phone": "0912345678",
            "position_id": "PY"
        },
        {
            "person_id": "C02",
            "full_name": "Trần Thị Bình",
            "email": "binh@example.com",
            "phone": "0987654321",
            "position_id": "HR"
        }
    ]

    print("1. Ghi danh sách mẫu ra file JSON")
    file_manager.write_json(filename, data)
    print("Đã ghi:", filename)
    print("Số bản ghi:", len(data))

    print("\n2. Đọc lại dữ liệu")
    result = file_manager.read_json(filename)
    for candidate in result:
        print(candidate["person_id"], candidate["full_name"],
              candidate["phone"], sep=" | ")

    print("\n3. So sánh với dữ liệu ban đầu")
    print("Dữ liệu trùng khớp:", result == data)

    print("\n4. Mở file bằng UTF-8 để kiểm tra tiếng Việt")
    file_path = demo_dir / filename
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    print(content)
    vietnamese_ok = all(candidate["full_name"] in content for candidate in data)
    print("Tên tiếng Việt được lưu nguyên dấu:", vietnamese_ok)
    print("File được lưu tại: tests/demo_json/candidates_sample.json")


if __name__ == "__main__":
    main()
