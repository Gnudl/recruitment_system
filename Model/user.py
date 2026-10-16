from models.person import Person
VALID_ROLES = ["Admin", "Staff"]

class User(Person):
   
    def __init__(
        self,
        person_id: str,
        full_name: str,
        email: str,
        phone: str,
        username: str,
        password: str,
        role: str = "Staff",
    ):
        super().__init__(person_id, full_name, email, phone)

        self._username = ""
        self._password_hash = ""
        self._role = ""

        self.username = username
        self.password = password
        self.role = role


    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, value: str):
        if not value or not str(value).strip():
            raise ValueError("Tên đăng nhập (username) không được để trống.")
        self._username = str(value).strip()


    @property
    def password_hash(self):
        return self._password_hash

    @password_hash.setter
    def password_hash(self, value: str):
        if not value or not str(value).strip():
            raise ValueError("Mật khẩu (password) không được để trống.")
        self._password_hash = str(value).strip()


    @property
    def role(self):
        return self._role

    @role.setter
    def role(self, value: str):
        val = str(value).strip() if value else ""
        if val not in self.VALID_ROLES:
            raise ValueError(f"Vai trò '{value}' không hợp lệ. Phải là một trong: {', '.join(self.VALID_ROLES)}")
        self._role = val

  
    def is_admin(self):
        return self._role == "Admin"

    def is_staff(self):
        return self._role == "Staff"


    def to_dict(self) -> dict:
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
        if self.is_admin():
            return "Quản trị viên (Admin)"
        return "Nhân viên nhân sự (Staff)"

    def __str__(self) -> str:
        return f"Tài khoản [{self._username}] - {self._full_name} ({self.get_role_display()})"

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            person_id=data.get("person_id", ""),
            full_name=data.get("full_name", ""),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            username=data.get("username", ""),
            password_hash=data.get("password", ""),
            role=data.get("role", "Staff"),
        )
