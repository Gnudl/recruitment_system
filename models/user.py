from models.person import Person


class User(Person):
    """Lớp User đại diện cho người dùng đăng nhập hệ thống (Admin hoặc Staff)."""

    ROLE_ADMIN = "Admin"
    ROLE_STAFF = "Staff"
    VALID_ROLES = [ROLE_ADMIN, ROLE_STAFF]

    def __init__(
        self,
        person_id,
        full_name,
        email,
        phone,
        username,
        password_hash,
        role = ROLE_STAFF,
    ):
        super().__init__(person_id, full_name, email, phone)

        self._username = ""
        self._password_hash = ""
        self._role = self.ROLE_STAFF

        self.username = username
        self.password_hash = password_hash
        self.role = role

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, value):
        if not value or not str(value).strip():
            raise ValueError("Tên đăng nhập (username) không được để trống.")
        self._username = str(value).strip()

    @property
    def password_hash(self):
        return self._password_hash

    @password_hash.setter
    def password_hash(self, value):
        if not value or not str(value).strip():
            raise ValueError("Mật khẩu băm (password_hash) không được để trống.")
        self._password_hash = str(value).strip()

    @property
    def role(self):
        return self._role

    @role.setter
    def role(self, value):
        val = str(value).strip() if value else ""
        if val not in self.VALID_ROLES:
            raise ValueError(f"Vai trò '{value}' không hợp lệ. Phải là một trong: {', '.join(self.VALID_ROLES)}")
        self._role = val

    def is_admin(self):
        return self._role == self.ROLE_ADMIN

    def is_staff(self):
        return self._role == self.ROLE_STAFF

    def to_dict(self):
        """Tuần tự hóa đối tượng User thành dictionary."""
        return {
            "person_id": self._person_id,
            "full_name": self._full_name,
            "email": self._email,
            "phone": self._phone,
            "username": self._username,
            "password_hash": self._password_hash,
            "role": self._role,
        }

    def get_role_display(self):
        """Hiển thị chức danh/vai trò của người dùng."""
        if self.is_admin():
            return "Quản trị viên (Admin)"
        return "Nhân viên nhân sự (Staff)"

    def __str__(self):
        return f"Tài khoản [{self._username}] - {self._full_name} ({self.get_role_display()})"

    @classmethod
    def from_dict(cls, data):
        """Khởi tạo đối tượng User từ dictionary."""
        return cls(
            person_id=data.get("person_id", ""),
            full_name=data.get("full_name", ""),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            username=data.get("username", ""),
            password_hash=data.get("password_hash", ""),
            role=data.get("role", cls.ROLE_STAFF),
        )
