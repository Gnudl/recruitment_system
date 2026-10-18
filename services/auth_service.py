import hashlib
import os
import hmac
import secrets
from typing import Optional, List, Dict

from models.user import User
from services.file_manager import FileManager


class AuthService:
    """
    Dịch vụ xác thực và phân quyền người dùng:
    - Băm và kiểm tra mật khẩu bằng SHA-256.
    - Quản lý phiên đăng nhập (session): login, logout, get_current_user.
    - Kiểm tra quyền hạn nghiêm ngặt ở tầng Service: is_admin, is_staff, has_role.
    - Tự động nạp và lưu trữ dữ liệu người dùng qua FileManager (data/users.json).
    - Tự động khởi tạo tài khoản mẫu (admin/admin123, staff/staff123) nếu file rỗng.
    """

    DEFAULT_USERS_FILE = "data/users.json"

    def __init__(self, file_manager: Optional[FileManager] = None, users_file: Optional[str] = None):
        self.file_manager = file_manager or FileManager()
        self.users_file = users_file or self.DEFAULT_USERS_FILE
        self._current_user: Optional[User] = None

        # Tự động nạp hoặc khởi tạo tài khoản ban đầu
        self._ensure_default_users()

    @staticmethod
    def hash_password(password: str) -> str:
        """PBKDF2 với salt riêng cho từng tài khoản."""
        if not password:
            return ""
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 200_000)
        return f"pbkdf2_sha256$200000${salt}${digest.hex()}"

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Kiểm tra mật khẩu nhập vào khớp với giá trị băm SHA-256."""
        if not password or not hashed:
            return False
        if hashed.startswith("pbkdf2_sha256$"):
            try:
                _, rounds, salt, digest = hashed.split("$")
                actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), int(rounds))
                return hmac.compare_digest(actual, bytes.fromhex(digest))
            except (ValueError, TypeError):
                return False
        # Tương thích tài khoản mẫu đã lưu từ phiên bản cũ.
        return hmac.compare_digest(hashlib.sha256(password.encode("utf-8")).hexdigest(), hashed)

    def _load_users(self) -> List[User]:
        """Đọc danh sách người dùng từ users.json."""
        raw_data = self.file_manager.read_json(self.users_file, default=[])
        users = []
        if not isinstance(raw_data, list):
            raise ValueError("users.json phải chứa một danh sách tài khoản.")
        for item in raw_data:
            try:
                users.append(User.from_dict(item))
            except (TypeError, ValueError, AttributeError) as exc:
                raise ValueError(f"Tài khoản số {len(users) + 1} bị lỗi: {exc}") from exc
        return users

    def _save_users(self, users: List[User]) -> None:
        """Ghi danh sách người dùng vào users.json một cách an toàn."""
        data = [u.to_dict() for u in users]
        self.file_manager.write_json(self.users_file, data, backup=True)

    def _ensure_default_users(self) -> None:
        """Khởi tạo tài khoản mẫu nếu users.json chưa có người dùng."""
        users = self._load_users()
        if not users:
            # Tạo sẵn 1 Admin và 1 Staff với mật khẩu đã băm SHA-256
            default_admin = User(
                person_id="U01",
                full_name="Quản trị viên Hệ thống",
                email="admin@recruitment.vn",
                phone="0901234567",
                username="admin",
                password_hash=self.hash_password("admin123"),
                role=User.ROLE_ADMIN,
            )
            default_staff = User(
                person_id="U02",
                full_name="Nhân viên Tuyển dụng",
                email="staff@recruitment.vn",
                phone="0987654321",
                username="staff",
                password_hash=self.hash_password("staff123"),
                role=User.ROLE_STAFF,
            )
            self._save_users([default_admin, default_staff])

    def login(self, username: str, password: str) -> Optional[User]:
        """
        Đăng nhập người dùng bằng username và password plaintext.
        Mật khẩu được băm SHA-256 trước khi đối soát.
        Trả về User nếu hợp lệ, None nếu thất bại.
        """
        if not username or not password:
            return None

        clean_username = username.strip()
        users = self._load_users()

        for user in users:
            if user.username.lower() == clean_username.lower():
                if self.verify_password(password, user.password_hash):
                    self._current_user = user
                    if not user.password_hash.startswith("pbkdf2_sha256$"):
                        user.password_hash = self.hash_password(password)
                        self._save_users(users)
                    return user
        return None

    def logout(self) -> None:
        """Đăng xuất người dùng hiện tại."""
        self._current_user = None

    def get_current_user(self) -> Optional[User]:
        """Lấy thông tin người dùng đang đăng nhập."""
        return self._current_user

    def is_logged_in(self) -> bool:
        """Kiểm tra có người dùng nào đang đăng nhập không."""
        return self._current_user is not None

    def has_role(self, role: str) -> bool:
        """Kiểm tra người dùng hiện tại có vai trò tương ứng không."""
        if not self._current_user:
            return False
        return self._current_user.role == role

    def is_admin(self) -> bool:
        """Kiểm tra người dùng hiện tại có quyền Admin không."""
        return self.has_role(User.ROLE_ADMIN)

    def is_staff(self) -> bool:
        """Kiểm tra người dùng hiện tại có quyền Staff không."""
        return self.has_role(User.ROLE_STAFF)

    def create_user(self, person_id: str, full_name: str, email: str, phone: str,
                    username: str, password: str, role: str = User.ROLE_STAFF) -> User:
        if not self.is_admin():
            raise PermissionError("Chỉ Quản trị viên được tạo tài khoản.")
        if len(password) < 8:
            raise ValueError("Mật khẩu phải có ít nhất 8 ký tự.")
        users = self._load_users()
        if any(u.username.casefold() == username.strip().casefold() or u.person_id.casefold() == person_id.strip().casefold() for u in users):
            raise ValueError("Tên đăng nhập hoặc mã tài khoản đã tồn tại.")
        user = User(person_id, full_name, email, phone, username, self.hash_password(password), role)
        self._save_users(users + [user])
        return user

    def change_password(self, old_password: str, new_password: str) -> None:
        if self._current_user is None:
            raise PermissionError("Vui lòng đăng nhập.")
        if not self.verify_password(old_password, self._current_user.password_hash):
            raise ValueError("Mật khẩu cũ không đúng.")
        if len(new_password) < 8:
            raise ValueError("Mật khẩu mới phải có ít nhất 8 ký tự.")
        users = self._load_users()
        for user in users:
            if user.username == self._current_user.username:
                user.password_hash = self.hash_password(new_password)
                self._current_user = user
                break
        self._save_users(users)
