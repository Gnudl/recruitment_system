from abc import ABC, abstractmethod
import re

# Regex chuẩn cho Email
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$')

# Regex cho số điện thoại di động Việt Nam: 10 chữ số, bắt đầu bằng 03, 05, 07, 08, 09
PHONE_REGEX = re.compile(r'^(03|05|07|08|09)\d{8}$')


class Person(ABC):
    """Lớp trừu tượng đại diện cho một con người trong hệ thống."""

    def __init__(self, person_id, full_name, email, phone):
        self._person_id = ""
        self._full_name = ""
        self._email = ""
        self._phone = ""

        # Thiết lập thông qua setter để thực hiện validation tự động
        self.person_id = person_id
        self.full_name = full_name
        self.email = email
        self.phone = phone

    @property
    def person_id(self):
        return self._person_id

    @person_id.setter
    def person_id(self, value):
        if not value or not str(value).strip():
            raise ValueError("Mã định danh (ID) không được để trống.")
        self._person_id = str(value).strip()

    @property
    def full_name(self):
        return self._full_name

    @full_name.setter
    def full_name(self, value):
        if not value or not str(value).strip():
            raise ValueError("Họ và tên không được để trống.")
        self._full_name = str(value).strip()

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        val = str(value).strip() if value else ""
        if not val or not EMAIL_REGEX.match(val):
            raise ValueError(f"Email không hợp lệ: '{value}'. Vui lòng nhập đúng định dạng (vd: user@example.com).")
        self._email = val

    @property
    def phone(self):
        return self._phone

    @phone.setter
    def phone(self, value):
        val = str(value).strip() if value else ""
        if not val or not PHONE_REGEX.match(val):
            raise ValueError(
                f"Số điện thoại không hợp lệ: '{value}'. Số điện thoại di động VN phải có đúng 10 số và bắt đầu bằng 03, 05, 07, 08 hoặc 09."
            )
        self._phone = val

    @abstractmethod
    def to_dict(self):
        """Chuyển đổi đối tượng thành dictionary để tuần tự hóa JSON."""
        pass

    @abstractmethod
    def get_role_display(self):
        """Trả về chuỗi hiển thị vai trò trong hệ thống."""
        pass
