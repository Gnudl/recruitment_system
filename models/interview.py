"""Lịch và kết quả phỏng vấn. Mỗi bản ghi giữ nguyên lịch sử một vòng."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Interview:
    interview_id: str
    candidate_id: str
    round_number: int
    starts_at: str
    interviewer: str
    outcome: str = "Chờ đánh giá"
    score: float | None = None
    notes: str = ""

    OUTCOMES = ("Chờ đánh giá", "Đạt", "Không đạt")

    def __post_init__(self):
        self.interview_id = self.interview_id.strip()
        self.candidate_id = self.candidate_id.strip()
        self.interviewer = self.interviewer.strip()
        if not all((self.interview_id, self.candidate_id, self.interviewer)):
            raise ValueError("Mã lịch, ứng viên và người phỏng vấn là bắt buộc.")
        if type(self.round_number) is not int or self.round_number not in (1, 2):
            raise ValueError("Vòng phỏng vấn phải là 1 hoặc 2.")
        try:
            datetime.strptime(self.starts_at, "%Y-%m-%d %H:%M")
        except ValueError as exc:
            raise ValueError("Ngày giờ phải theo dạng YYYY-MM-DD HH:MM.") from exc
        if self.outcome not in self.OUTCOMES:
            raise ValueError("Kết quả phỏng vấn không hợp lệ.")
        if self.score is not None:
            self.score = float(self.score)
            if not 0 <= self.score <= 100:
                raise ValueError("Điểm phải từ 0 đến 100.")
        if self.outcome != "Chờ đánh giá" and self.score is None:
            raise ValueError("Cần nhập điểm khi có kết quả.")
        self.notes = self.notes.strip()

    def to_dict(self):
        return vars(self).copy()

    @classmethod
    def from_dict(cls, data):
        return cls(**data)
