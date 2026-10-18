"""Lấy tin tuyển dụng công khai qua API, dùng thư viện chuẩn Python."""

import json
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from services.file_manager import FileManager


class JobCrawler:
    API_URL = "https://remotive.com/api/remote-jobs"
    DEFAULT_CRAWLED_FILE = "data/crawled_jobs.json"

    def __init__(self, file_manager=None, crawled_file=None):
        self.file_manager = file_manager or FileManager()
        self.crawled_file = crawled_file or self.DEFAULT_CRAWLED_FILE

    def normalize_job_data(self, payload):
        rows = payload.get("jobs", []) if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            raise ValueError("API không trả về danh sách tin tuyển dụng.")
        result = []
        for row in rows:
            if not isinstance(row, dict) or not row.get("title"):
                continue
            result.append({
                "job_id": str(row.get("id", "")),
                "title": str(row["title"]).strip(),
                "company": str(row.get("company_name", "")).strip(),
                "location": str(row.get("candidate_required_location", "")).strip(),
                "url": str(row.get("url", "")).strip(),
                "published_date": str(row.get("publication_date", ""))[:10],
                "source": self.API_URL,
                "fetched_at": datetime.now().isoformat(timespec="seconds"),
            })
        return result

    def fetch_jobs(self, keyword="python", source_url=None):
        url = source_url or f"{self.API_URL}?{urlencode({'search': keyword, 'limit': 10})}"
        try:
            with urlopen(Request(url, headers={"User-Agent": "StudentRecruitmentProject/1.0"}), timeout=8) as response:
                payload = json.load(response)
            jobs = self.normalize_job_data(payload)[:10]
            self.save_crawled_jobs(jobs)
            return True, jobs, f"Đã lưu {len(jobs)} tin từ API."
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            return False, [], f"Không lấy được dữ liệu API: {exc}"

    def save_crawled_jobs(self, jobs, filepath=None):
        self.file_manager.write_json(filepath or self.crawled_file, jobs, backup=True)

    def load_saved_crawled_jobs(self, filepath=None):
        rows = self.file_manager.read_json(filepath or self.crawled_file, default=[])
        if not isinstance(rows, list):
            raise ValueError("Dữ liệu API đã lưu không hợp lệ.")
        return rows
