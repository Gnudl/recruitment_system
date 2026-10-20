from pathlib import Path
from tempfile import mkdtemp
from unittest.mock import patch
import json
import sys

project_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_dir))

from services.file_manager import FileManager, JSONCorruptedError


def main():
    # Mỗi lần chạy dùng thư mục riêng, giữ lại để xem bản sao lưu.
    demo_root = project_dir / "tests" / "demo_backup"
    demo_root.mkdir(parents=True, exist_ok=True)
    folder = Path(mkdtemp(prefix="run_", dir=demo_root))
    file_manager = FileManager(folder)
    results = []

    print("1. Đọc tệp không tồn tại")
    result = file_manager.read_json("missing.json")
    passed = result == [] and json.loads(
        (folder / "missing.json").read_text(encoding="utf-8")
    ) == []
    results.append(passed)
    print("Dữ liệu:", result)
    print("Tệp đã được tạo:", (folder / "missing.json").exists())
    print("Đạt:", passed)

    print("\n2. Đọc tệp rỗng")
    (folder / "empty.json").write_text("", encoding="utf-8")
    result = file_manager.read_json("empty.json")
    passed = result == []
    results.append(passed)
    print("Dữ liệu:", result)
    print("Đạt:", passed)

    print("\n3. JSON sai định dạng, không có backup")
    broken_path = folder / "broken.json"
    broken_path.write_text("{broken", encoding="utf-8")
    before = broken_path.read_bytes()
    rejected = False
    try:
        file_manager.read_json("broken.json")
    except JSONCorruptedError:
        rejected = True
        print("Lỗi: JSONCorruptedError - JSON hỏng, không có backup hợp lệ")
    passed = rejected and broken_path.read_bytes() == before
    results.append(passed)
    print("Tệp gốc giữ nguyên:", broken_path.read_bytes() == before)
    print("Đạt:", passed)

    old_data = [{"person_id": "C01", "full_name": "Nguyễn Văn An"}]
    new_data = [{"person_id": "C01", "full_name": "Nguyễn Văn Bình"}]

    print("\n4. Ghi đè và sao lưu dữ liệu cũ")
    file_manager.write_json("candidates.json", old_data)
    file_manager.write_json("candidates.json", new_data)
    backup_path = folder / "backups" / "candidates.json.bak"
    backup_data = json.loads(backup_path.read_text(encoding="utf-8"))
    passed = file_manager.read_json("candidates.json") == new_data and backup_data == old_data
    results.append(passed)
    print("Dữ liệu mới:", file_manager.read_json("candidates.json"))
    print("Dữ liệu backup:", backup_data)
    print("Đạt:", passed)

    print("\n5. Mô phỏng lỗi khi thay thế tệp chính")
    file_manager.write_json("write_error.json", old_data)
    target = folder / "write_error.json"
    before = target.read_bytes()
    rejected = False
    with patch("services.file_manager.os.replace",
               side_effect=PermissionError("Lỗi ghi giả lập")):
        try:
            file_manager.write_json("write_error.json", new_data)
        except PermissionError as error:
            rejected = True
            print("Lỗi:", error)
    temp_files = list(folder.glob(".write_error.json.*.tmp"))
    passed = rejected and target.read_bytes() == before and not temp_files
    results.append(passed)
    print("Tệp gốc giữ nguyên:", target.read_bytes() == before)
    print("Số tệp tạm còn lại:", len(temp_files))
    print("Đạt:", passed)

    print("\n6. Tệp chính hỏng, có backup hợp lệ")
    (folder / "candidates.json").write_text("{broken", encoding="utf-8")
    result = file_manager.read_json("candidates.json")
    saved_data = json.loads((folder / "candidates.json").read_text(encoding="utf-8"))
    passed = result == old_data and saved_data == old_data
    results.append(passed)
    print("Dữ liệu phục hồi:", result)
    print("Đạt:", passed)

    print("\nSố tình huống đạt:", sum(results), "/", len(results))
    print("Thư mục sao lưu:", (folder / "backups").relative_to(project_dir))
    for path in sorted((folder / "backups").iterdir()):
        print(path.name)


if __name__ == "__main__":
    main()
