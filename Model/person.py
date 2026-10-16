from abc import ABC, abstractmethod
import re

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$')
PHONE_REGEX = re.compile(r'^(03|05|07|08|09)\d{8}$')

class Person(ABC):
    def __init__(self, person_id: str, full_name: str, email:str, phone:str):
        self._person_id = ""
        self._full_name = ""
        self._email = ""
        self._phone = ""

        self.person_id = person_id
        self.full_name = full_name
        self.email = email
        self.phone = phone

    @property
    def person_id (self):
        return self._person_id 

    @person_id.setter
    def person_id(self, value:str):
        if not value or not str(value).strip():
            raise ValueError("Mã định danh (ID) không được để trống !")
        self._person_id = str(value).strip()


    @property
    def full_name(self):
        return self._full_name

    @full_name.setter
    def full_name(self, value: str):
        if not value or not str(value).strip():
            raise ValueError("Họ tên không được để trống !")
        self._full_name = str(value).strip()
        
    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value: str):
        val = str(value).strip() if value else ""
        if not val or not EMAIL_REGEX.match(val):
            raise ValueError(f"Email không hợp lệ: '{value}'. Vui lòng nhập đúng (vd: user@example.com).")
        self._email = val 

    @property
    def phone(self):
        return self._phone

    @phone.setter
    def phone(self, value: str):
        val = str(value).strip() if value else ""
        if not val or not PHONE_REGEX.match(val):
            raise ValueError(f"Số điện thoại không hợp lệ: '{value}'. SDT VN có 10 số và bắt đầu bằng 03, 05, 07, 08, 09.")
        self._phone = val

    @abstractmethod
    def to_dict(self):
        pass

    @abstractmethod
    def get_role_display(self):
        pass

    def __str__(self):
        return (
            f"[Vai trò: {self.get_role_display()}] "
            f"Họ tên: {self.full_name} | "
            f"ID: {self.person_id} | "
            f"Email: {self.email}"
        )
