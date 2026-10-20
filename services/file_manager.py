import os
import sys
import json
import shutil
import tempfile
from datetime import datetime


class JSONCorruptedError(Exception):
    """Ngoại lệ ném ra khi file JSON bị hỏng cú pháp và không thể khôi phục từ bản backup."""
    pass


def get_base_dir():
    """Xác định thư mục gốc của ứng dụng một cách an toàn"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class FileManager:
    """Đọc, ghi và sao lưu file JSON."""

    def __init__(self, base_dir = None, backup_dir = None):
        self.base_dir = os.path.abspath(base_dir) if base_dir else get_base_dir()

        if backup_dir:
            self.backup_dir = os.path.abspath(backup_dir)
        else:
            # Đường dẫn backup chuẩn duy nhất theo cấu trúc dự án: backups/ tại gốc
            self.backup_dir = os.path.join(self.base_dir, "backups")

        # Đảm bảo thư mục backup tồn tại
        os.makedirs(self.backup_dir, exist_ok=True)

    def resolve_path(self, filepath):
        """Chuyển đổi đường dẫn tương đối thành tuyệt đối dựa trên base_dir."""
        if os.path.isabs(filepath):
            return filepath
        return os.path.abspath(os.path.join(self.base_dir, filepath))

    def find_latest_valid_backup(self, filepath):
        """Tìm kiếm bản sao lưu (.bak) hợp lệ gần nhất của file được chỉ định trong thư mục backups."""
        filename = os.path.basename(filepath)
        name_no_ext = os.path.splitext(filename)[0]

        candidates = []
        if os.path.exists(self.backup_dir):
            for entry in os.listdir(self.backup_dir):
                # Khớp mẫu: name_no_ext*.bak hoặc name_no_ext*.json.bak
                if entry.startswith(name_no_ext) and (entry.endswith(".bak") or entry.endswith(".bak.latest")):
                    full_path = os.path.join(self.backup_dir, entry)
                    if os.path.isfile(full_path):
                        candidates.append(full_path)

        # Sắp xếp theo thời gian chỉnh sửa mới nhất trước (mtime giảm dần)
        candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)

        for candidate_path in candidates:
            # Kiểm tra xem bản backup có đọc được JSON hợp lệ và không rỗng hay không
            if os.path.getsize(candidate_path) == 0:
                continue
            try:
                with open(candidate_path, "r", encoding="utf-8") as bf:
                    content = bf.read().strip()
                    if content:
                        json.loads(content)
                        return candidate_path
            except (json.JSONDecodeError, OSError):
                # Bỏ qua bản backup hỏng, tiếp tục tìm bản cũ hơn còn nguyên vẹn
                continue

        return None

    def create_backup(self, filepath):
        """Tạo bản sao lưu cho file hiện tại vào thư mục backup."""
        abs_path = self.resolve_path(filepath)
        if not os.path.exists(abs_path) or os.path.getsize(abs_path) == 0:
            return None

        os.makedirs(self.backup_dir, exist_ok=True)
        filename = os.path.basename(abs_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_filename = f"{filename}_{timestamp}.bak"
        backup_path = os.path.join(self.backup_dir, backup_filename)

        # Sao chép dữ liệu hiện tại sang file backup
        shutil.copy2(abs_path, backup_path)

        # Đồng thời cập nhật bản sao lưu 'latest' để dễ truy vết
        latest_path = os.path.join(self.backup_dir, f"{filename}.bak")
        shutil.copy2(abs_path, latest_path)

        return backup_path

    def restore_backup(self, backup_filepath, target_filepath):
        """Khôi phục dữ liệu từ bản backup sang file đích bằng cơ chế ghi nguyên tử (atomic write)."""
        abs_target = self.resolve_path(target_filepath)
        with open(backup_filepath, "r", encoding="utf-8") as bf:
            data = json.load(bf)
        # Ghi lại vào file đích nhưng không tạo backup mới trong lúc khôi phục
        self.write_json(abs_target, data, backup=False)

    def read_json(self, filepath, default = None):
        """Đọc dữ liệu từ file JSON một cách an toàn"""
        abs_path = self.resolve_path(filepath)
        effective_default = [] if default is None else default

        # 1. Trường hợp file chưa tồn tại
        if not os.path.exists(abs_path):
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            self.write_json(abs_path, effective_default, backup=False)
            return effective_default

        # 2. Trường hợp file 0-byte
        if os.path.getsize(abs_path) == 0:
            return effective_default

        # 3. Đọc và phân tích cú pháp JSON
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return effective_default
                return json.loads(content)
        except json.JSONDecodeError as decode_err:
            # 4. JSON sai cú pháp -> Tự động tìm kiếm bản backup gần nhất
            backup_file = self.find_latest_valid_backup(abs_path)
            if backup_file:
                # Phục hồi dữ liệu từ bản backup
                self.restore_backup(backup_file, abs_path)
                with open(abs_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                raise JSONCorruptedError(
                    f"File dữ liệu '{abs_path}' bị lỗi cú pháp JSON ({decode_err}), "
                    f"và không tìm thấy bất kỳ bản backup .bak hợp lệ nào để khôi phục."
                )

    def write_json(self, filepath, data, backup = True):
        """Ghi JSON qua file tạm và sao lưu dữ liệu cũ."""
        abs_path = self.resolve_path(filepath)
        target_dir = os.path.dirname(abs_path)
        os.makedirs(target_dir, exist_ok=True)

        # Sao lưu dữ liệu cũ (nếu có và được yêu cầu)
        if backup and os.path.exists(abs_path) and os.path.getsize(abs_path) > 0:
            self.create_backup(abs_path)

        # Tạo file tạm .tmp trong cùng thư mục để đảm bảo cùng phân vùng đĩa (Atomic trên OS)
        fd, temp_path = tempfile.mkstemp(
            dir=target_dir,
            prefix=f".{os.path.basename(abs_path)}.",
            suffix=".tmp"
        )

        try:
            # Ghi dữ liệu vào file tạm
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                json.dump(data, tmp_file, ensure_ascii=False, indent=2)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())

            # Kiểm tra tính toàn vẹn của dữ liệu trong file tạm
            with open(temp_path, "r", encoding="utf-8") as verify_file:
                json.load(verify_file)

            # Hoán đổi nguyên tử thay thế file chính
            os.replace(temp_path, abs_path)
        except Exception as write_err:
            # Dọn dẹp file tạm nếu có lỗi xảy ra trong quá trình ghi
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            raise write_err
