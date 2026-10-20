import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from models.candidate import Candidate
from models.job_position import JobPosition
from models.interview import Interview
from services.auth_service import AuthService
from services.file_manager import FileManager, JSONCorruptedError
from services.recruitment_mgr import RecruitmentManager
from services.job_crawler import JobCrawler


class RecruitmentFlowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fm = FileManager(base_dir=self.tmp.name)
        self.auth = AuthService(self.fm)
        self.manager = RecruitmentManager(self.fm, auth_service=self.auth)
        self.admin = self.auth.login("admin", "admin123")
        self.manager.create_job(JobPosition("PY", "Python Developer", "IT", 100, 200, 2, requirements="Python"))
        self.candidate = Candidate("C1", "Nguyễn An", "an@example.com", "0912345678", "PY", source="Giới thiệu")

    def tearDown(self):
        self.tmp.cleanup()

    def test_01_login_and_password_migration(self):
        self.assertTrue(self.auth.get_current_user().password_hash.startswith("pbkdf2_sha256$"))
        self.auth.logout()
        self.assertIsNone(self.auth.login("admin", "wrong"))
        self.assertIsNotNone(self.auth.login("admin", "admin123"))

    def test_02_candidate_crud_and_search(self):
        self.manager.create_candidate(self.candidate)
        self.assertEqual(len(self.manager.search_candidates("nguyễn")), 1)
        self.candidate.full_name = "Nguyễn Bình"
        self.manager.update_candidate(self.candidate)
        self.assertEqual(self.manager.get_candidate_by_id("C1").full_name, "Nguyễn Bình")
        self.manager.delete_candidate("C1")
        self.assertEqual(self.manager.get_candidates(), [])

    def test_03_invalid_email_and_phone(self):
        with self.assertRaises(ValueError):
            Candidate("C2", "A", "bad@", "0912345678", "PY")
        with self.assertRaises(ValueError):
            Candidate("C2", "A", "a@example.com", "123", "PY")

    def test_04_duplicate_and_missing_job(self):
        self.manager.create_candidate(self.candidate)
        with self.assertRaises(ValueError):
            self.manager.create_candidate(self.candidate)
        with self.assertRaises(ValueError):
            self.manager.create_candidate(Candidate("C2", "B", "b@example.com", "0987654321", "UNKNOWN"))

    def test_05_staff_permissions(self):
        self.auth.login("staff", "staff123")
        with self.assertRaises(PermissionError):
            self.manager.create_candidate(self.candidate)
        with self.assertRaises(PermissionError):
            self.manager.create_job(JobPosition("QA", "QA", "IT", 1, 2, 1))

    def test_06_interview_history_and_result(self):
        self.manager.create_candidate(self.candidate)
        first = Interview("I1", "C1", 1, "2026-10-20 09:00", "Giảng viên")
        self.manager.save_interview(first)
        first.outcome, first.score = "Đạt", 80
        self.manager.save_interview(first)
        second = Interview("I2", "C1", 2, "2026-10-22 09:00", "Nhân sự", "Đạt", 90)
        self.manager.save_interview(second)
        self.assertEqual(len(self.manager.get_interviews()), 2)
        self.assertEqual(self.manager.get_candidate_by_id("C1").status, Candidate.STATUS_DAT_OFFER)

    def test_07_round_two_requires_pass(self):
        self.manager.create_candidate(self.candidate)
        with self.assertRaises(ValueError):
            self.manager.save_interview(Interview("I2", "C1", 2, "2026-10-22 09:00", "Nhân sự"))

    def test_08_schedule_conflict(self):
        self.manager.create_candidate(self.candidate)
        self.manager.create_candidate(Candidate("C2", "B", "b@example.com", "0987654321", "PY"))
        self.manager.save_interview(Interview("I1", "C1", 1, "2026-10-20 09:00", "A"))
        with self.assertRaises(ValueError):
            self.manager.save_interview(Interview("I2", "C2", 1, "2026-10-20 09:00", "A"))

    def test_09_source_statistics(self):
        self.manager.create_candidate(self.candidate)
        self.manager.save_interview(Interview("I1", "C1", 1, "2026-10-20 09:00", "A", "Đạt", 80))
        self.manager.save_interview(Interview("I2", "C1", 2, "2026-10-21 09:00", "B", "Đạt", 90))
        self.assertEqual(self.manager.get_source_statistics()["Giới thiệu"]["rate"], 100.0)

    def test_10_account_creation_and_change_password(self):
        self.auth.create_user("U3", "Nhân viên Ba", "ba@example.com", "0987654321", "ba", "password123")
        self.auth.login("ba", "password123")
        self.auth.change_password("password123", "newpassword123")
        self.auth.logout()
        self.assertIsNone(self.auth.login("ba", "password123"))
        self.assertIsNotNone(self.auth.login("ba", "newpassword123"))

    def test_11_corrupt_json_is_reported(self):
        self.fm.write_json("data/test.json", [{"a": 1}], backup=False)
        with open(os.path.join(self.tmp.name, "data", "test.json"), "w", encoding="utf8") as handle:
            handle.write("{broken")
        with self.assertRaises(JSONCorruptedError):
            self.fm.read_json("data/test.json")

    def test_12_api_normalization_and_persistence(self):
        crawler = JobCrawler(self.fm)
        payload = json.dumps({"jobs": [{"id": 1, "title": "Python", "company_name": "Demo"}]}).encode()
        with patch("services.job_crawler.urlopen", return_value=io.BytesIO(payload)):
            ok, rows, message = crawler.fetch_jobs()
        self.assertTrue(ok)
        self.assertEqual(rows[0]["source"], crawler.API_URL)
        self.assertEqual(len(crawler.load_saved_crawled_jobs()), 1)

    def test_13_export_csv(self):
        self.manager.create_candidate(self.candidate)
        target = os.path.join(self.tmp.name, "report.csv")
        self.manager.export_candidates_to_csv(target)
        with open(target, "r", encoding="utf-8-sig") as handle:
            self.assertIn("Nguyễn An", handle.read())

    def test_14_invalid_date(self):
        with self.assertRaises(ValueError):
            Interview("I1", "C1", 1, "2026-02-30 12:00", "A")

    def test_15_pipeline_counts_reached_stages(self):
        self.manager.create_candidate(self.candidate)
        self.manager.save_interview(Interview("I1", "C1", 1, "2026-10-20 09:00", "A", "Đạt", 80))
        self.manager.save_interview(Interview("I2", "C1", 2, "2026-10-21 09:00", "B", "Đạt", 90))
        self.assertEqual([count for _, count in self.manager.get_pipeline_statistics()], [1, 1, 1, 1, 1])

    def test_16_staff_can_evaluate_but_not_edit_profile(self):
        self.manager.create_candidate(self.candidate)
        self.auth.login("staff", "staff123")
        self.manager.save_interview(Interview("I1", "C1", 1, "2026-10-20 09:00", "A", "Đạt", 80))
        with self.assertRaises(PermissionError):
            self.manager.update_candidate(self.candidate)

    def test_17_interview_history_cannot_be_deleted(self):
        self.manager.create_candidate(self.candidate)
        self.manager.save_interview(Interview("I1", "C1", 1, "2026-10-20 09:00", "A", "Đạt", 80))
        with self.assertRaises(ValueError):
            self.manager.delete_interview("I1")
        with self.assertRaises(ValueError):
            self.manager.delete_candidate("C1")

    def test_18_offer_respects_job_quota(self):
        self.manager.update_job(JobPosition("PY", "Python Developer", "IT", 100, 200, 1))
        self.manager.create_candidate(self.candidate)
        self.manager.create_candidate(Candidate("C2", "B", "b@example.com", "0987654321", "PY"))
        for candidate_id, suffix in [("C1", "1"), ("C2", "2")]:
            self.manager.save_interview(Interview("R1" + suffix, candidate_id, 1,
                f"2026-10-2{suffix} 09:00", "A", "Đạt", 80))
        self.manager.save_interview(Interview("R21", "C1", 2, "2026-10-23 09:00", "B", "Đạt", 90))
        with self.assertRaises(ValueError):
            self.manager.save_interview(Interview("R22", "C2", 2, "2026-10-24 09:00", "B", "Đạt", 90))


if __name__ == "__main__":
    unittest.main()
