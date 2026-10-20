class JobPosition:
    """Lớp JobPosition đại diện cho một vị trí/chức danh tuyển dụng trong công ty."""

    STATUS_DANG_TUYEN = "Đang tuyển"
    STATUS_TAM_DUNG = "Tạm dừng"
    STATUS_DA_DONG = "Đã đóng"

    VALID_STATUSES = [STATUS_DANG_TUYEN, STATUS_TAM_DUNG, STATUS_DA_DONG]

    def __init__(
        self,
        position_id,
        title,
        department,
        min_salary,
        max_salary,
        quota,
        status = STATUS_DANG_TUYEN,
        requirements = "",
    ):
        self._position_id = ""
        self._title = ""
        self._department = ""
        self._min_salary = 0.0
        self._max_salary = 0.0
        self._quota = 1
        self._status = self.STATUS_DANG_TUYEN

        self.position_id = position_id
        self.title = title
        self.department = department
        # Đặt mức lương qua phương thức thiết lập kiểm tra cặp giá trị
        self.set_salary_range(min_salary, max_salary)
        self.quota = quota
        self.status = status
        self.requirements = requirements

    @property
    def requirements(self):
        return self._requirements

    @requirements.setter
    def requirements(self, value):
        self._requirements = str(value or "").strip()

    @property
    def position_id(self):
        return self._position_id

    @position_id.setter
    def position_id(self, value):
        if not value or not str(value).strip():
            raise ValueError("Mã vị trí (position_id) không được để trống.")
        self._position_id = str(value).strip()

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        if not value or not str(value).strip():
            raise ValueError("Tiêu đề vị trí tuyển dụng không được để trống.")
        self._title = str(value).strip()

    @property
    def department(self):
        return self._department

    @department.setter
    def department(self, value):
        if not value or not str(value).strip():
            raise ValueError("Phòng ban không được để trống.")
        self._department = str(value).strip()

    @property
    def min_salary(self):
        return self._min_salary

    @min_salary.setter
    def min_salary(self, value):
        try:
            val = float(value)
        except (ValueError, TypeError):
            raise ValueError("Mức lương tối thiểu phải là số.")
        if val < 0:
            raise ValueError("Mức lương tối thiểu không được là số âm.")
        if self._max_salary > 0 and val > self._max_salary:
            raise ValueError(f"Mức lương tối thiểu ({val}) không được lớn hơn lương tối đa ({self._max_salary}).")
        self._min_salary = val

    @property
    def max_salary(self):
        return self._max_salary

    @max_salary.setter
    def max_salary(self, value):
        try:
            val = float(value)
        except (ValueError, TypeError):
            raise ValueError("Mức lương tối đa phải là số.")
        if val < 0:
            raise ValueError("Mức lương tối đa không được là số âm.")
        if val < self._min_salary:
            raise ValueError(f"Mức lương tối đa ({val}) không được nhỏ hơn lương tối thiểu ({self._min_salary}).")
        self._max_salary = val

    def set_salary_range(self, min_salary, max_salary):
        """Thiết lập đồng thời cả hai mức lương để kiểm tra ràng buộc min <= max."""
        try:
            min_val = float(min_salary)
            max_val = float(max_salary)
        except (ValueError, TypeError):
            raise ValueError("Mức lương phải là một số.")
        if min_val < 0 or max_val < 0:
            raise ValueError("Mức lương không được là số âm.")
        if min_val > max_val:
            raise ValueError(f"Mức lương tối thiểu ({min_val}) không được lớn hơn lương tối đa ({max_val}).")
        self._min_salary = min_val
        self._max_salary = max_val

    @property
    def quota(self):
        return self._quota

    @quota.setter
    def quota(self, value):
        try:
            if isinstance(value, bool) or str(value).strip() != str(int(value)):
                raise ValueError
            val = int(value)
        except (ValueError, TypeError):
            raise ValueError("Chỉ tiêu tuyển dụng (quota) phải là số nguyên.")
        if val <= 0:
            raise ValueError(f"Chỉ tiêu tuyển dụng phải là số nguyên dương > 0 (nhận được: {value}).")
        self._quota = val

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        val = str(value).strip() if value else ""
        if val not in self.VALID_STATUSES:
            raise ValueError(
                f"Trạng thái vị trí '{value}' không hợp lệ. Phải là một trong: {', '.join(self.VALID_STATUSES)}"
            )
        self._status = val

    def to_dict(self):
        """Tuần tự hóa đối tượng JobPosition thành dictionary."""
        return {
            "position_id": self._position_id,
            "title": self._title,
            "department": self._department,
            "min_salary": self._min_salary,
            "max_salary": self._max_salary,
            "quota": self._quota,
            "status": self._status,
            "requirements": self._requirements,
        }

    @classmethod
    def from_dict(cls, data):
        """Khởi tạo đối tượng JobPosition từ dictionary."""
        return cls(
            position_id=data.get("position_id", ""),
            title=data.get("title", ""),
            department=data.get("department", ""),
            min_salary=data.get("min_salary", 0.0),
            max_salary=data.get("max_salary", 0.0),
            quota=data.get("quota", 1),
            status=data.get("status", cls.STATUS_DANG_TUYEN),
            requirements=data.get("requirements", ""),
        )

    def __str__(self):
        return (
            f"Vị trí [{self._position_id}] {self._title} ({self._department}) | "
            f"Lương: {self._min_salary:,.0f} - {self._max_salary:,.0f} VNĐ | Chỉ tiêu: {self._quota} | Trạng thái: {self._status}"
        )
