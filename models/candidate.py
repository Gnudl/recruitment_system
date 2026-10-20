from models.person import Person


class Candidate(Person):
    """Lớp Candidate đại diện cho hồ sơ ứng viên tuyển dụng."""

    # Danh mục các vòng/trạng thái tuyển dụng chuẩn
    STATUS_NOP_HO_SO = "Nộp hồ sơ"
    STATUS_DUYET_CV = "Duyệt CV"
    STATUS_PV_VONG_1 = "Phỏng vấn vòng 1"
    STATUS_PV_VONG_2 = "Phỏng vấn vòng 2"
    STATUS_DAT_OFFER = "Đạt/Offer"
    STATUS_LOAI = "Loại"

    VALID_STATUSES = [
        STATUS_NOP_HO_SO,
        STATUS_DUYET_CV,
        STATUS_PV_VONG_1,
        STATUS_PV_VONG_2,
        STATUS_DAT_OFFER,
        STATUS_LOAI,
    ]

    def __init__(
        self,
        person_id,
        full_name,
        email,
        phone,
        position_id,
        experience_years = 0.0,
        status = STATUS_NOP_HO_SO,
        interview_score = 0.0,
        source = "Khác",
    ):
        # Gọi hàm khởi tạo của lớp cha Person
        super().__init__(person_id, full_name, email, phone)

        self._position_id = ""
        self._experience_years = 0.0
        self._status = self.STATUS_NOP_HO_SO
        self._interview_score = 0.0
        self._source = ""

        # Gán qua setter để kiểm tra ràng buộc nghiệp vụ
        self.position_id = position_id
        self.experience_years = experience_years
        self.status = status
        self.interview_score = interview_score
        self.source = source

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Nguồn ứng viên không được để trống.")
        self._source = value.strip()

    @property
    def position_id(self):
        return self._position_id

    @position_id.setter
    def position_id(self, value):
        if not value or not str(value).strip():
            raise ValueError("Mã vị trí ứng tuyển không được để trống.")
        self._position_id = str(value).strip()

    @property
    def experience_years(self):
        return self._experience_years

    @experience_years.setter
    def experience_years(self, value):
        try:
            val = float(value)
        except (ValueError, TypeError):
            raise ValueError("Số năm kinh nghiệm phải là số.")
        if val < 0:
            raise ValueError("Số năm kinh nghiệm không thể là số âm.")
        self._experience_years = val

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        val = str(value).strip() if value else ""
        if val not in self.VALID_STATUSES:
            raise ValueError(
                f"Trạng thái '{value}' không hợp lệ. Phải là một trong: {', '.join(self.VALID_STATUSES)}"
            )
        self._status = val

    @property
    def interview_score(self):
        return self._interview_score

    @interview_score.setter
    def interview_score(self, value):
        try:
            val = float(value)
        except (ValueError, TypeError):
            raise ValueError("Điểm phỏng vấn phải là một số.")
        if not (0.0 <= val <= 100.0):
            raise ValueError(f"Điểm phỏng vấn phải nằm trong khoảng từ 0 đến 100 (nhận được: {value}).")
        self._interview_score = val

    def to_dict(self):
        """Tuần tự hóa đối tượng Candidate thành dictionary."""
        return {
            "person_id": self._person_id,
            "full_name": self._full_name,
            "email": self._email,
            "phone": self._phone,
            "position_id": self._position_id,
            "experience_years": self._experience_years,
            "status": self._status,
            "interview_score": self._interview_score,
            "source": self._source,
        }

    def get_role_display(self):
        """Hiển thị vai trò của Candidate."""
        return "Ứng viên"

    def __str__(self):
        return (
            f"Ứng viên [{self._person_id}] {self._full_name} | Vị trí: {self._position_id} | "
            f"Trạng thái: {self._status} | Điểm: {self._interview_score} | KN: {self._experience_years} năm"
        )

    @classmethod
    def from_dict(cls, data):
        """Khởi tạo đối tượng Candidate từ dictionary."""
        return cls(
            person_id=data.get("person_id", ""),
            full_name=data.get("full_name", ""),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            position_id=data.get("position_id", ""),
            experience_years=data.get("experience_years", 0.0),
            status=data.get("status", cls.STATUS_NOP_HO_SO),
            interview_score=data.get("interview_score", 0.0),
            source=data.get("source", "Khác"),
        )
