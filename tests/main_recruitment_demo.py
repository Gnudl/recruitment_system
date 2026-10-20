from pathlib import Path
import sys

# Lấy thư mục gốc của dự án từ vị trí file trong tests.
project_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_dir))

from tempfile import TemporaryDirectory

from models.candidate import Candidate
from models.job_position import JobPosition
from services.file_manager import FileManager
from services.recruitment_mgr import RecruitmentManager


def show_candidates(candidates):
    for candidate in candidates:
        print(candidate.person_id, candidate.full_name,
              candidate.position_id, candidate.phone, sep=" | ")
    print("Số ứng viên:", len(candidates))


def main():
    # Dùng thư mục tạm để không thay đổi dữ liệu của nhóm.
    with TemporaryDirectory(dir=project_dir) as folder:
        file_manager = FileManager(folder)
        manager = RecruitmentManager(file_manager)

        manager.create_job(
            JobPosition("PY", "Python Developer", "IT", 10000000, 15000000, 2)
        )
        manager.create_job(
            JobPosition("HR", "Nhân viên tuyển dụng", "HR", 8000000, 12000000, 1)
        )

        print("1. Thêm ứng viên")
        candidate = Candidate("C01", "Nguyễn Văn An",
                              "an@example.com", "0912345678", "PY")
        manager.create_candidate(candidate)
        manager.create_candidate(
            Candidate("C02", "Trần Thị Bình",
                      "binh@example.com", "0987654321", "HR")
        )
        show_candidates(manager.get_candidates())

        print("\n2. Tìm tên có chữ Nguyễn")
        show_candidates(manager.search_candidates("nguyễn"))

        print("\n3. Lọc ứng viên theo vị trí PY")
        show_candidates(manager.filter_candidates(position_id="PY"))

        print("\n4. Cập nhật số điện thoại C01")
        candidate.phone = "0901234567"
        manager.update_candidate(candidate)
        result = manager.get_candidate_by_id("C01")
        print(result.person_id, result.full_name, result.phone, sep=" | ")

        print("\n5. Thêm trùng mã C01")
        try:
            manager.create_candidate(candidate)
        except ValueError as error:
            print("Lỗi:", error)
        print("Số ứng viên sau khi thử:", len(manager.get_candidates()))

        print("\n6. Thêm ứng viên vào vị trí NONE")
        try:
            manager.create_candidate(
                Candidate("C03", "Lê Văn Cường",
                          "cuong@example.com", "0934567890", "NONE")
            )
        except ValueError as error:
            print("Lỗi:", error)
        print("Số ứng viên sau khi thử:", len(manager.get_candidates()))

        print("\n7. Xóa ứng viên C02")
        print("Kết quả xóa:", manager.delete_candidate("C02"))
        show_candidates(manager.get_candidates())


if __name__ == "__main__":
    main()
