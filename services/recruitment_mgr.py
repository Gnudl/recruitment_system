import csv
import os
from typing import Optional, List

from models.candidate import Candidate
from models.job_position import JobPosition
from models.user import User
from models.interview import Interview
from services.file_manager import FileManager


class RecruitmentManager:
    """CRUD, lịch phỏng vấn, phân quyền và thống kê từ dữ liệu JSON."""

    DEFAULT_CANDIDATES_FILE = "data/candidates.json"
    DEFAULT_JOBS_FILE = "data/jobs.json"
    DEFAULT_INTERVIEWS_FILE = "data/interviews.json"

    CSV_HEADERS = [
        "ID",
        "Họ tên",
        "Email",
        "Số điện thoại",
        "Vị trí",
        "Kinh nghiệm",
        "Trạng thái",
        "Điểm",
        "Nguồn ứng viên",
    ]

    def __init__(
        self,
        file_manager: Optional[FileManager] = None,
        candidates_file: Optional[str] = None,
        jobs_file: Optional[str] = None,
        interviews_file: Optional[str] = None,
        auth_service=None,
    ):
        self.file_manager = file_manager or FileManager()
        self.candidates_file = candidates_file or self.DEFAULT_CANDIDATES_FILE
        self.jobs_file = jobs_file or self.DEFAULT_JOBS_FILE
        self.interviews_file = interviews_file or self.DEFAULT_INTERVIEWS_FILE
        self.auth_service = auth_service

    def _require_admin(self):
        if self.auth_service is not None and not self.auth_service.is_admin():
            raise PermissionError("Chức năng này chỉ dành cho Quản trị viên.")

    def _require_login(self):
        if self.auth_service is not None and not self.auth_service.is_logged_in():
            raise PermissionError("Vui lòng đăng nhập.")

    def _read_list(self, filename):
        rows = self.file_manager.read_json(filename, default=[])
        if not isinstance(rows, list):
            raise ValueError(f"Dữ liệu trong {filename} phải là danh sách JSON.")
        return rows

    # =========================================================================
    # CANDIDATE CRUD & OPERATIONS
    # =========================================================================

    def get_candidates(self) -> List[Candidate]:
        """Lấy toàn bộ danh sách ứng viên từ file JSON."""
        raw_list = self._read_list(self.candidates_file)
        candidates = []
        for item in raw_list:
            try:
                candidates.append(Candidate.from_dict(item))
            except (TypeError, ValueError, AttributeError) as exc:
                raise ValueError(f"Hồ sơ ứng viên số {len(candidates) + 1} bị lỗi: {exc}") from exc
        return candidates

    def _save_candidates(self, candidates: List[Candidate]) -> None:
        """Lưu danh sách ứng viên vào file JSON an toàn (có auto-backup)."""
        data = [c.to_dict() for c in candidates]
        self.file_manager.write_json(self.candidates_file, data, backup=True)

    def get_candidate_by_id(self, candidate_id: str) -> Optional[Candidate]:
        """Tìm kiếm ứng viên theo ID."""
        if not candidate_id:
            return None
        clean_id = str(candidate_id).strip().lower()
        for c in self.get_candidates():
            if c.person_id.lower() == clean_id:
                return c
        return None

    def create_candidate(self, candidate: Candidate) -> Candidate:
        """
        Thêm mới một ứng viên:
        - Kiểm tra trùng ID (không phân biệt hoa thường).
        - Ghi vào candidates.json có sao lưu .bak tự động.
        """
        if not isinstance(candidate, Candidate):
            raise TypeError("Dữ liệu phải là một đối tượng Candidate.")
        self._require_admin()
        job = self.get_job_by_id(candidate.position_id)
        if job is None or job.status != JobPosition.STATUS_DANG_TUYEN:
            raise ValueError("Vị trí ứng tuyển không tồn tại hoặc không còn tuyển.")

        candidates = self.get_candidates()
        # Kiểm tra trùng ID
        for existing in candidates:
            if existing.person_id.lower() == candidate.person_id.lower():
                raise ValueError(f"Mã ứng viên '{candidate.person_id}' đã tồn tại trong hệ thống. Không thể thêm trùng.")

        candidates.append(candidate)
        self._save_candidates(candidates)
        return candidate

    def update_candidate(self, candidate: Candidate) -> Candidate:
        """Cập nhật thông tin ứng viên đã có trong hệ thống."""
        if not isinstance(candidate, Candidate):
            raise TypeError("Dữ liệu phải là một đối tượng Candidate.")
        self._require_admin()
        job = self.get_job_by_id(candidate.position_id)
        if job is None:
            raise ValueError("Vị trí ứng tuyển không tồn tại.")

        candidates = self.get_candidates()
        found = False
        for i, existing in enumerate(candidates):
            if existing.person_id.lower() == candidate.person_id.lower():
                if existing.position_id != candidate.position_id and any(
                    row.candidate_id == candidate.person_id for row in self.get_interviews()
                ):
                    raise ValueError("Không đổi vị trí của ứng viên đã có lịch phỏng vấn.")
                candidates[i] = candidate
                found = True
                break

        if not found:
            raise ValueError(f"Không tìm thấy ứng viên có mã '{candidate.person_id}' để cập nhật.")

        self._save_candidates(candidates)
        return candidate

    def delete_candidate(self, candidate_id: str, current_user: Optional[User] = None) -> bool:
        """
        Xóa ứng viên khỏi hệ thống:
        - Ràng buộc phân quyền: Chỉ Admin mới có quyền xóa. Staff bị từ chối với PermissionError.
        """
        self._require_admin()
        if current_user is not None:
            if not current_user.is_admin():
                raise PermissionError("Nhân viên (Staff) không có quyền xóa ứng viên. Chỉ Quản trị viên (Admin) mới có quyền này.")
        if any(i.candidate_id.casefold() == str(candidate_id).strip().casefold() for i in self.get_interviews()):
            raise ValueError("Không thể xóa ứng viên đã có lịch phỏng vấn; cần giữ lịch sử.")

        candidates = self.get_candidates()
        initial_count = len(candidates)
        candidates = [c for c in candidates if c.person_id.lower() != str(candidate_id).strip().lower()]

        if len(candidates) == initial_count:
            raise ValueError(f"Không tìm thấy ứng viên có mã '{candidate_id}' để xóa.")

        self._save_candidates(candidates)
        return True

    def search_candidates(self, keyword: str, candidates: Optional[List[Candidate]] = None) -> List[Candidate]:
        """
        Tìm kiếm ứng viên theo họ tên hoặc số điện thoại:
        - Không phân biệt hoa thường (case-insensitive).
        - Hỗ trợ tiếng Việt Unicode (ví dụ: 'nguyễn' khớp cả 'Nguyễn Văn A' và 'Trần NGUYỄN').
        """
        source = candidates if candidates is not None else self.get_candidates()
        if not keyword or not str(keyword).strip():
            return source

        term = str(keyword).strip().lower()
        results = []
        for c in source:
            # Khớp tên hoặc số điện thoại
            if term in c.full_name.lower() or term in c.phone:
                results.append(c)
        return results

    def filter_candidates(
        self,
        position_id: Optional[str] = None,
        status: Optional[str] = None,
        candidates: Optional[List[Candidate]] = None,
    ) -> List[Candidate]:
        """Lọc ứng viên kết hợp theo vị trí tuyển dụng và trạng thái."""
        source = candidates if candidates is not None else self.get_candidates()
        results = source

        if position_id and str(position_id).strip() and str(position_id).strip() != "Tất cả":
            pos = str(position_id).strip().lower()
            results = [c for c in results if c.position_id.lower() == pos]

        if status and str(status).strip() and str(status).strip() != "Tất cả":
            stat = str(status).strip().lower()
            results = [c for c in results if c.status.lower() == stat]

        return results

    def query_candidates(
        self,
        keyword: Optional[str] = None,
        position_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Candidate]:
        """Tìm kiếm và lọc kết hợp trên danh sách ứng viên."""
        results = self.get_candidates()
        if keyword:
            results = self.search_candidates(keyword, results)
        if position_id or status:
            results = self.filter_candidates(position_id, status, results)
        return results

    # =========================================================================
    # JOB POSITION CRUD & OPERATIONS
    # =========================================================================

    def get_jobs(self) -> List[JobPosition]:
        """Lấy toàn bộ danh sách vị trí tuyển dụng."""
        raw_list = self._read_list(self.jobs_file)
        jobs = []
        for item in raw_list:
            try:
                jobs.append(JobPosition.from_dict(item))
            except (TypeError, ValueError, AttributeError) as exc:
                raise ValueError(f"Vị trí tuyển dụng số {len(jobs) + 1} bị lỗi: {exc}") from exc
        return jobs

    def _save_jobs(self, jobs: List[JobPosition]) -> None:
        """Lưu danh sách vị trí tuyển dụng an toàn."""
        data = [j.to_dict() for j in jobs]
        self.file_manager.write_json(self.jobs_file, data, backup=True)

    def get_job_by_id(self, position_id: str) -> Optional[JobPosition]:
        """Tìm vị trí tuyển dụng theo mã position_id."""
        if not position_id:
            return None
        clean_id = str(position_id).strip().lower()
        for j in self.get_jobs():
            if j.position_id.lower() == clean_id:
                return j
        return None

    def create_job(self, job: JobPosition) -> JobPosition:
        """Thêm mới vị trí tuyển dụng (kiểm tra trùng mã)."""
        if not isinstance(job, JobPosition):
            raise TypeError("Dữ liệu phải là một đối tượng JobPosition.")
        self._require_admin()

        jobs = self.get_jobs()
        for existing in jobs:
            if existing.position_id.lower() == job.position_id.lower():
                raise ValueError(f"Mã vị trí tuyển dụng '{job.position_id}' đã tồn tại trong hệ thống.")

        jobs.append(job)
        self._save_jobs(jobs)
        return job

    def update_job(self, job: JobPosition) -> JobPosition:
        """Cập nhật thông tin vị trí tuyển dụng."""
        if not isinstance(job, JobPosition):
            raise TypeError("Dữ liệu phải là một đối tượng JobPosition.")
        self._require_admin()

        jobs = self.get_jobs()
        found = False
        for i, existing in enumerate(jobs):
            if existing.position_id.lower() == job.position_id.lower():
                jobs[i] = job
                found = True
                break

        if not found:
            raise ValueError(f"Không tìm thấy vị trí tuyển dụng có mã '{job.position_id}' để cập nhật.")

        self._save_jobs(jobs)
        return job

    def delete_job(self, position_id: str, current_user: Optional[User] = None) -> bool:
        """
        Xóa vị trí tuyển dụng:
        - Chỉ Admin mới được quyền xóa.
        - Kiểm tra xem có ứng viên nào đang ứng tuyển vào vị trí này không.
        """
        self._require_admin()
        if current_user is not None and not current_user.is_admin():
            raise PermissionError("Chỉ Quản trị viên (Admin) mới có quyền xóa vị trí tuyển dụng.")

        clean_id = str(position_id).strip().lower()

        # Kiểm tra ràng buộc tham chiếu ứng viên
        for c in self.get_candidates():
            if c.position_id.lower() == clean_id:
                raise ValueError(
                    f"Không thể xóa vị trí '{position_id}' vì hiện đang có ứng viên [{c.person_id} - {c.full_name}] ứng tuyển."
                )

        jobs = self.get_jobs()
        initial_count = len(jobs)
        jobs = [j for j in jobs if j.position_id.lower() != clean_id]

        if len(jobs) == initial_count:
            raise ValueError(f"Không tìm thấy vị trí tuyển dụng có mã '{position_id}' để xóa.")

        self._save_jobs(jobs)
        return True

    # =========================================================================
    # FUNNEL STATISTICS
    # =========================================================================

    def get_interviews(self) -> List[Interview]:
        result = []
        for index, row in enumerate(self._read_list(self.interviews_file), 1):
            try:
                result.append(Interview.from_dict(row))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Lịch phỏng vấn số {index} bị lỗi: {exc}") from exc
        return result

    def save_interview(self, interview: Interview) -> Interview:
        self._require_login()
        if self.get_candidate_by_id(interview.candidate_id) is None:
            raise ValueError("Ứng viên không tồn tại.")
        rows = self.get_interviews()
        if interview.round_number == 1 and any(x.candidate_id == interview.candidate_id and x.round_number == 2 for x in rows):
            previous = next((x for x in rows if x.candidate_id == interview.candidate_id and x.round_number == 1), None)
            if previous and (interview.outcome != previous.outcome or interview.score != previous.score):
                raise ValueError("Không đổi kết quả vòng 1 sau khi đã có lịch vòng 2.")
        for existing in rows:
            if existing.interview_id != interview.interview_id and existing.candidate_id == interview.candidate_id and existing.round_number == interview.round_number:
                raise ValueError("Ứng viên đã có lịch cho vòng này.")
            if existing.interview_id != interview.interview_id and existing.candidate_id == interview.candidate_id and existing.starts_at == interview.starts_at:
                raise ValueError("Ứng viên đã có lịch vào thời điểm này.")
            if existing.interview_id != interview.interview_id and existing.interviewer.casefold() == interview.interviewer.casefold() and existing.starts_at == interview.starts_at:
                raise ValueError("Người phỏng vấn đã có lịch vào thời điểm này.")
        if interview.round_number == 2 and interview.outcome == "Đạt":
            candidate = self.get_candidate_by_id(interview.candidate_id)
            job = self.get_job_by_id(candidate.position_id)
            already_offered = sum(c.position_id == candidate.position_id and c.status == Candidate.STATUS_DAT_OFFER
                                  and c.person_id != candidate.person_id for c in self.get_candidates())
            if already_offered >= job.quota:
                raise ValueError("Vị trí đã đủ chỉ tiêu tuyển dụng.")
        for index, existing in enumerate(rows):
            if existing.interview_id == interview.interview_id:
                if existing.candidate_id != interview.candidate_id or existing.round_number != interview.round_number:
                    raise ValueError("Không đổi ứng viên hoặc vòng của lịch đã tạo.")
                if existing.outcome != "Chờ đánh giá" and interview.outcome == "Chờ đánh giá":
                    raise ValueError("Không thể xóa kết quả đã đánh giá.")
                rows[index] = interview
                break
        else:
            if interview.round_number == 2:
                previous = next((x for x in rows if x.candidate_id == interview.candidate_id and x.round_number == 1), None)
                if previous is None or previous.outcome != "Đạt":
                    raise ValueError("Chỉ lập vòng 2 sau khi vòng 1 đạt.")
            rows.append(interview)
        self.file_manager.write_json(self.interviews_file, [x.to_dict() for x in rows], backup=True)
        self._sync_candidate_status(interview.candidate_id)
        return interview

    def delete_interview(self, interview_id: str) -> None:
        self._require_admin()
        rows = self.get_interviews()
        target = next((x for x in rows if x.interview_id == interview_id), None)
        if target is None:
            raise ValueError("Không tìm thấy lịch phỏng vấn.")
        if target.outcome != "Chờ đánh giá":
            raise ValueError("Không thể xóa lịch đã có kết quả; hãy giữ lịch sử đánh giá.")
        self.file_manager.write_json(self.interviews_file, [x.to_dict() for x in rows if x.interview_id != interview_id], backup=True)
        self._sync_candidate_status(target.candidate_id)

    def _sync_candidate_status(self, candidate_id: str) -> None:
        candidate = self.get_candidate_by_id(candidate_id)
        records = {x.round_number: x for x in self.get_interviews() if x.candidate_id == candidate_id}
        if not records:
            candidate.status = Candidate.STATUS_NOP_HO_SO
            candidate.interview_score = 0
        else:
            latest = records.get(2) or records.get(1)
            if latest.outcome == "Không đạt":
                candidate.status = Candidate.STATUS_LOAI
            elif latest.round_number == 2 and latest.outcome == "Đạt":
                candidate.status = Candidate.STATUS_DAT_OFFER
            elif latest.round_number == 2:
                candidate.status = Candidate.STATUS_PV_VONG_2
            else:
                candidate.status = Candidate.STATUS_PV_VONG_1
            candidate.interview_score = latest.score or 0
        # Ghi trực tiếp vì nhân viên được phép đánh giá, nhưng không sửa hồ sơ gốc.
        candidates = self.get_candidates()
        for index, item in enumerate(candidates):
            if item.person_id == candidate_id:
                candidates[index] = candidate
        self._save_candidates(candidates)

    def get_source_statistics(self) -> dict:
        candidates = self.get_candidates()
        sources = {}
        for candidate in candidates:
            item = sources.setdefault(candidate.source, {"total": 0, "passed": 0})
            item["total"] += 1
            if candidate.status == Candidate.STATUS_DAT_OFFER:
                item["passed"] += 1
        return {name: {**item, "rate": round(item["passed"] * 100 / item["total"], 1)} for name, item in sources.items()}

    def get_pipeline_statistics(self) -> list[tuple[str, int]]:
        """Đếm số hồ sơ từng đi đến mỗi mốc; dữ liệu mới dùng lịch phỏng vấn."""
        candidates = self.get_candidates()
        interviews = self.get_interviews()
        round_one = {x.candidate_id for x in interviews if x.round_number == 1}
        round_two = {x.candidate_id for x in interviews if x.round_number == 2}
        screened = sum(c.status != Candidate.STATUS_NOP_HO_SO for c in candidates)
        reached_one = sum(c.person_id in round_one or c.status in (
            Candidate.STATUS_PV_VONG_1, Candidate.STATUS_PV_VONG_2, Candidate.STATUS_DAT_OFFER
        ) for c in candidates)
        reached_two = sum(c.person_id in round_two or c.status in (
            Candidate.STATUS_PV_VONG_2, Candidate.STATUS_DAT_OFFER
        ) for c in candidates)
        offers = sum(c.status == Candidate.STATUS_DAT_OFFER for c in candidates)
        return [("Nộp hồ sơ", len(candidates)), ("Đã duyệt CV", screened),
                ("Đến vòng 1", reached_one), ("Đến vòng 2", reached_two),
                ("Đạt/Offer", offers)]

    # =========================================================================
    # CSV EXPORT
    # =========================================================================

    def export_candidates_to_csv(self, filepath: str, candidates: Optional[List[Candidate]] = None) -> str:
        """
        Xuất danh sách ứng viên ra file CSV với bảng mã UTF-8-SIG (tương thích hoàn hảo với Excel).
        Nếu không truyền danh sách candidates thì xuất toàn bộ ứng viên hiện có.
        """
        source = candidates if candidates is not None else self.get_candidates()
        abs_path = self.file_manager.resolve_path(filepath)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)

        with open(abs_path, "w", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.writer(csvfile)
            # Ghi dòng tiêu đề
            writer.writerow(self.CSV_HEADERS)

            # Ghi từng dòng dữ liệu
            for c in source:
                writer.writerow([
                    c.person_id,
                    c.full_name,
                    c.email,
                    c.phone,
                    c.position_id,
                    c.experience_years,
                    c.status,
                    c.interview_score,
                    c.source,
                ])

        return abs_path
