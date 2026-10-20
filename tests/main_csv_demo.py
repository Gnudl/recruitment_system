from pathlib import Path
import csv
import sys

project_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_dir))

from models.candidate import Candidate
from services.file_manager import FileManager
from services.recruitment_mgr import RecruitmentManager


def main():
    # Dữ liệu chạy thử được lưu riêng trong tests.
    demo_dir = project_dir / "tests" / "demo_csv"
    file_manager = FileManager(demo_dir)
    manager = RecruitmentManager(file_manager)

    candidates = [
        Candidate("C01", "Nguyễn Văn An",
                  "an@example.com", "0912345678", "PY"),
        Candidate("C02", "Trần Thị Bình",
                  "binh@example.com", "0987654321", "HR")
    ]

    print("1. Xuất danh sách ứng viên")
    path = manager.export_candidates_to_csv(
        "output/candidates_sample.csv", candidates
    )
    print("Đã xuất: candidates_sample.csv")
    print("Số ứng viên nguồn:", len(candidates))

    print("\n2. Đọc lại file CSV")
    with open(path, "r", newline="", encoding="utf-8-sig") as file:
        rows = list(csv.reader(file))

    print("Các cột:", " | ".join(rows[0]))
    for row in rows[1:]:
        print(row[0], row[1], row[3], sep=" | ")

    print("Tổng số dòng, gồm tiêu đề:", len(rows))
    print("Số dòng dữ liệu:", len(rows) - 1)
    print("Số dòng khớp số ứng viên:", len(rows) - 1 == len(candidates))
    print("Thứ tự cột đúng:", rows[0] == manager.CSV_HEADERS)
    names = [row[1] for row in rows[1:]]
    print("Tên tiếng Việt đọc lại đúng:",
          names == [candidate.full_name for candidate in candidates])

    print("\n3. Xuất danh sách rỗng")
    empty_path = manager.export_candidates_to_csv(
        "output/candidates_empty.csv", []
    )
    with open(empty_path, "r", newline="", encoding="utf-8-sig") as file:
        empty_rows = list(csv.reader(file))

    print("Đã xuất: candidates_empty.csv")
    print("Tổng số dòng:", len(empty_rows))
    print("Số dòng dữ liệu:", len(empty_rows) - 1)
    print("File chỉ chứa tiêu đề:", empty_rows == [manager.CSV_HEADERS])
    print("\nThư mục kết quả: tests/demo_csv/output")


if __name__ == "__main__":
    main()
