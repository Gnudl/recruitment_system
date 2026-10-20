from pathlib import Path
from getpass import getpass as hidden_password
import json
import os
import sys
import unicodedata

if os.name == "nt":
    import msvcrt

from models.candidate import Candidate
from models.job_position import JobPosition
from models.interview import Interview
from services.file_manager import FileManager, JSONCorruptedError
from services.auth_service import AuthService
from services.recruitment_mgr import RecruitmentManager
from services.job_crawler import JobCrawler


def getpass(prompt):
    # Hiện dấu * khi nhập mật khẩu trong terminal Windows.
    if os.name != "nt" or not sys.stdin.isatty():
        return hidden_password(prompt)
    print(prompt, end="", flush=True)
    password = []
    while True:
        char = msvcrt.getwch()
        if char in ("\r", "\n"):
            print()
            return "".join(password)
        if char == "\x03":
            print()
            raise KeyboardInterrupt
        if char in ("\x00", "\xe0"):
            msvcrt.getwch()
        elif char == "\b":
            if password:
                password.pop()
                print("\b \b", end="", flush=True)
        elif char.isprintable():
            password.append(char)
            print("*", end="", flush=True)


def read_value(label, current=None):
    if current is None:
        return input(label + ": ").strip()
    value = input(f"{label} [{current}]: ").strip()
    return value if value else str(current)


def confirm():
    return input("Nhập y để xác nhận: ").strip().lower() == "y"


def show_table(headers, rows):
    rows = [[unicodedata.normalize("NFC", str(value)).replace("\n", " ").replace("\r", " ")
             for value in row] for row in rows]
    widths = [max(len(header), max((len(row[index]) for row in rows), default=0))
              for index, header in enumerate(headers)]
    print(" | ".join(header.ljust(width) for header, width in zip(headers, widths)))
    for row in rows:
        print(" | ".join(value.ljust(width) for value, width in zip(row, widths)))


def show_items(items):
    if items and isinstance(items[0], JobPosition):
        headers = ["Mã vị trí", "Tên vị trí", "Phòng ban", "Lương (VNĐ)", "Chỉ tiêu", "Trạng thái"]
        rows = [[item.position_id, item.title, item.department,
                 f"{item.min_salary:,.0f} - {item.max_salary:,.0f}",
                 item.quota, item.status] for item in items]
        show_table(headers, rows)
    elif items and isinstance(items[0], Candidate):
        headers = ["Mã UV", "Họ tên", "Vị trí", "Trạng thái", "Điểm", "KN (năm)"]
        rows = [[item.person_id, item.full_name, item.position_id,
                 item.status, item.interview_score, item.experience_years] for item in items]
        show_table(headers, rows)
    elif items and isinstance(items[0], dict):
        headers = list(items[0])
        show_table(headers, [[item.get(key, "") for key in headers] for item in items])
    else:
        for item in items:
            print(item)
    print("Số bản ghi:", len(items))


def require_admin(auth_service):
    if not auth_service.is_admin():
        raise PermissionError("Chỉ quản trị viên được dùng chức năng này.")


def input_job(current=None):
    if current:
        print("Để trống để giữ giá trị cũ.")
        position_id = current.position_id
    else:
        position_id = read_value("Mã vị trí")
    title = read_value("Tên vị trí", current.title if current else None)
    department = read_value("Phòng ban", current.department if current else None)
    min_salary = float(read_value("Lương tối thiểu", current.min_salary if current else None))
    max_salary = float(read_value("Lương tối đa", current.max_salary if current else None))
    quota = int(read_value("Chỉ tiêu", current.quota if current else None))
    print("Trạng thái:", ", ".join(JobPosition.VALID_STATUSES))
    status = read_value("Trạng thái", current.status if current else "Đang tuyển")
    requirements = read_value("Yêu cầu", current.requirements if current else "")
    return JobPosition(position_id, title, department, min_salary,
                       max_salary, quota, status, requirements)


def input_candidate(current=None):
    if current:
        print("Để trống để giữ giá trị cũ.")
        person_id = current.person_id
    else:
        person_id = read_value("Mã ứng viên")
    full_name = read_value("Họ tên", current.full_name if current else None)
    email = read_value("Email", current.email if current else None)
    phone = read_value("Số điện thoại", current.phone if current else None)
    position_id = read_value("Mã vị trí", current.position_id if current else None)
    experience_years = float(read_value("Số năm kinh nghiệm", current.experience_years if current else 0))
    source = read_value("Nguồn ứng viên", current.source if current else "Khác")
    print("Trạng thái:", ", ".join(Candidate.VALID_STATUSES))
    status = read_value("Trạng thái", current.status if current else "Nộp hồ sơ")
    interview_score = current.interview_score if current else 0
    return Candidate(person_id, full_name, email, phone, position_id,
                     experience_years, status, interview_score, source)


def select_candidates(manager):
    keyword = read_value("Tên hoặc số điện thoại (trống để lấy tất cả)")
    position_id = read_value("Mã vị trí (trống để không lọc)")
    print("Trạng thái:", ", ".join(Candidate.VALID_STATUSES))
    status = read_value("Trạng thái (trống để không lọc)")
    return manager.query_candidates(keyword, position_id, status)


def input_interview(manager):
    interview_id = read_value("Mã lịch")
    current = next((item for item in manager.get_interviews()
                    if item.interview_id == interview_id), None)
    if current:
        print("Cập nhật lịch đã có. Để trống để giữ giá trị cũ.")
        candidate_id = current.candidate_id
        round_number = current.round_number
    else:
        candidate_id = read_value("Mã ứng viên")
        round_number = int(read_value("Vòng phỏng vấn (1 hoặc 2)"))
    starts_at = read_value("Ngày giờ (YYYY-MM-DD HH:MM)", current.starts_at if current else None)
    interviewer = read_value("Người phỏng vấn", current.interviewer if current else None)
    print("Kết quả:", ", ".join(Interview.OUTCOMES))
    outcome = read_value("Kết quả", current.outcome if current else "Chờ đánh giá")
    score_text = read_value("Điểm (trống nếu chưa có)",
                            current.score if current and current.score is not None else "")
    score = float(score_text) if score_text else None
    notes = read_value("Ghi chú", current.notes if current else "")
    return Interview(interview_id, candidate_id, round_number,
                     starts_at, interviewer, outcome, score, notes)


def file_menu(file_manager, auth_service):
    require_admin(auth_service)
    files = ["data/jobs.json", "data/candidates.json",
             "data/interviews.json", "data/users.json", "data/crawled_jobs.json"]
    for index, filename in enumerate(files, 1):
        print(index, filename)
    index = int(read_value("Chọn tệp")) - 1
    if index < 0 or index >= len(files):
        raise ValueError("Lựa chọn tệp không hợp lệ.")
    filename = files[index]
    print("1. Đọc JSON")
    print("2. Tạo bản sao lưu")
    print("3. Phục hồi từ bản sao lưu hợp lệ gần nhất")
    choice = read_value("Chọn thao tác")
    if choice == "1":
        rows = file_manager.read_json(filename)
        # Không in giá trị băm mật khẩu ra terminal.
        if filename == "data/users.json":
            rows = [{key: value for key, value in row.items()
                     if key != "password_hash"} for row in rows]
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    elif choice == "2":
        path = file_manager.create_backup(filename)
        print("Bản sao lưu:", path if path else "Tệp chưa tồn tại hoặc rỗng.")
    elif choice == "3":
        path = file_manager.find_latest_valid_backup(filename)
        if path is None:
            print("Không có bản sao lưu hợp lệ.")
        else:
            print("Bản sao:", path)
            print("Nội dung tệp chính sẽ được thay bằng bản sao này.")
            if confirm():
                file_manager.restore_backup(path, filename)
                print("Đã phục hồi. Vui lòng đăng nhập lại.")
                auth_service.logout()
    else:
        print("Lựa chọn không hợp lệ.")


def menu():
    print("\nQUẢN LÝ TUYỂN DỤNG")
    print("1. Xem vị trí tuyển dụng")
    print("2. Thêm vị trí tuyển dụng")
    print("3. Sửa vị trí tuyển dụng")
    print("4. Xóa vị trí tuyển dụng")
    print("5. Xem ứng viên")
    print("6. Thêm ứng viên")
    print("7. Sửa ứng viên")
    print("8. Xóa ứng viên")
    print("9. Tìm kiếm và lọc ứng viên")
    print("10. Xem lịch phỏng vấn")
    print("11. Thêm lịch hoặc cập nhật kết quả phỏng vấn")
    print("12. Xóa lịch chưa có kết quả")
    print("13. Thống kê tuyển dụng")
    print("14. Xuất CSV (toàn bộ hoặc theo bộ lọc)")
    print("15. Đọc JSON, sao lưu và phục hồi (Admin)")
    print("16. Tạo tài khoản (Admin)")
    print("17. Đổi mật khẩu")
    print("18. Lấy tin tuyển dụng từ API")
    print("19. Xem tin tuyển dụng đã lưu")
    print("20. Đăng xuất")
    print("0. Thoát")


def main(base_dir=None):
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent
    file_manager = FileManager(base_dir)
    auth_service = AuthService(file_manager)
    manager = RecruitmentManager(file_manager, auth_service=auth_service)
    crawler = JobCrawler(file_manager)
    print("Dữ liệu được lưu tự động sau mỗi thao tác thành công.")

    while True:
        try:
            if not auth_service.is_logged_in():
                print("\n1. Đăng nhập")
                print("0. Thoát")
                choice = read_value("Chọn")
                if choice == "0":
                    break
                if choice != "1":
                    print("Lựa chọn không hợp lệ.")
                    continue
                username = read_value("Tên đăng nhập")
                password = getpass("Mật khẩu: ")
                user = auth_service.login(username, password)
                if user is None:
                    print("Tên đăng nhập hoặc mật khẩu không đúng.")
                    continue
                print("Đăng nhập thành công:", user.full_name, "-", user.role)

            menu()
            choice = read_value("Chọn")
            if choice == "0":
                break
            elif choice == "1":
                show_items(manager.get_jobs())
            elif choice == "2":
                require_admin(auth_service)
                manager.create_job(input_job())
                print("Đã thêm vị trí.")
            elif choice == "3":
                require_admin(auth_service)
                current = manager.get_job_by_id(read_value("Mã vị trí cần sửa"))
                if current is None:
                    raise ValueError("Không tìm thấy vị trí.")
                manager.update_job(input_job(current))
                print("Đã cập nhật vị trí.")
            elif choice == "4":
                require_admin(auth_service)
                position_id = read_value("Mã vị trí cần xóa")
                if confirm():
                    manager.delete_job(position_id)
                    print("Đã xóa vị trí.")
            elif choice == "5":
                show_items(manager.get_candidates())
            elif choice == "6":
                require_admin(auth_service)
                manager.create_candidate(input_candidate())
                print("Đã thêm ứng viên.")
            elif choice == "7":
                require_admin(auth_service)
                current = manager.get_candidate_by_id(read_value("Mã ứng viên cần sửa"))
                if current is None:
                    raise ValueError("Không tìm thấy ứng viên.")
                manager.update_candidate(input_candidate(current))
                print("Đã cập nhật ứng viên.")
            elif choice == "8":
                require_admin(auth_service)
                person_id = read_value("Mã ứng viên cần xóa")
                if confirm():
                    manager.delete_candidate(person_id)
                    print("Đã xóa ứng viên.")
            elif choice == "9":
                show_items(select_candidates(manager))
            elif choice == "10":
                show_items([item.to_dict() for item in manager.get_interviews()])
            elif choice == "11":
                manager.save_interview(input_interview(manager))
                print("Đã lưu lịch và kết quả phỏng vấn.")
            elif choice == "12":
                require_admin(auth_service)
                interview_id = read_value("Mã lịch cần xóa")
                if confirm():
                    manager.delete_interview(interview_id)
                    print("Đã xóa lịch.")
            elif choice == "13":
                for status, count in manager.get_pipeline_statistics():
                    print(status + ":", count)
                print("Thống kê theo nguồn:")
                for source, values in manager.get_source_statistics().items():
                    print(source, "- Tổng:", values["total"],
                          "- Đạt:", values["passed"], "- Tỷ lệ:", values["rate"], "%")
            elif choice == "14":
                candidates = select_candidates(manager)
                filepath = read_value("Đường dẫn CSV", "output/candidates.csv")
                path = Path(file_manager.resolve_path(filepath))
                if path.suffix.lower() != ".csv":
                    raise ValueError("Tên tệp xuất phải có đuôi .csv.")
                if path.exists():
                    print("Tệp đã có. Ghi đè?")
                    if not confirm():
                        continue
                print("Đã xuất:", manager.export_candidates_to_csv(filepath, candidates))
                print("Số ứng viên:", len(candidates))
            elif choice == "15":
                file_menu(file_manager, auth_service)
            elif choice == "16":
                require_admin(auth_service)
                person_id = read_value("Mã tài khoản")
                full_name = read_value("Họ tên")
                email = read_value("Email")
                phone = read_value("Số điện thoại")
                username = read_value("Tên đăng nhập")
                password = getpass("Mật khẩu (ít nhất 8 ký tự): ")
                role = read_value("Vai trò Admin hoặc Staff", "Staff")
                auth_service.create_user(person_id, full_name, email, phone,
                                         username, password, role)
                print("Đã tạo tài khoản.")
            elif choice == "17":
                old_password = getpass("Mật khẩu cũ: ")
                new_password = getpass("Mật khẩu mới: ")
                if new_password != getpass("Nhập lại mật khẩu mới: "):
                    raise ValueError("Mật khẩu nhập lại không khớp.")
                auth_service.change_password(old_password, new_password)
                print("Đã đổi mật khẩu.")
            elif choice == "18":
                keyword = read_value("Từ khóa tuyển dụng", "python")
                success, jobs, message = crawler.fetch_jobs(keyword)
                print(message)
                if success:
                    show_items(jobs)
            elif choice == "19":
                show_items(crawler.load_saved_crawled_jobs())
            elif choice == "20":
                auth_service.logout()
                print("Đã đăng xuất.")
            else:
                print("Lựa chọn không hợp lệ.")
        except (ValueError, TypeError, OSError, JSONCorruptedError) as error:
            print("Lỗi:", error)
        except (EOFError, KeyboardInterrupt):
            print("\nĐã dừng chương trình.")
            break
    auth_service.logout()
    print("Đã thoát.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, JSONCorruptedError) as error:
        print("Không thể mở dữ liệu:", error)
