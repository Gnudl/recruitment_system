import re
DATE_REGEX = re.compile(r'^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/\d{4}$')
VALID_RESULTS = ["Chưa có", "Đạt", "Không đạt", "Cần phỏng vấn lại"]


class Interview:  # quan ly thong tin phong van va quan ly
    def __init__(self, interview_id: str, candidate_id: str, date: str, round_name: str, result: str = "Chua co", notes: str = ""):
        self._interview_id = ""
        self._candidate_id = ""
        self._date = ""
        self._round_name = ""
        self._result = ""
        self._notes = ""

        self.interview_id = interview_id
        self.candidate_id = candidate_id
        self.date = date
        self.round_name = round_name
        self.result = result
        self.notes = notes  #ghi chu danh gia ung vien 

    @property
    def interview_id(self):
        return self._interview_id

    @interview_id.setter
    def interview_id(self, value: str):
        if not value or not str(value).strip():
            raise ValueError("Mã buổi phỏng vấn không được để trống !")
        self._interview_id = str(value).strip()

 
    @property
    def candidate_id(self):
        return self._candidate_id

    @candidate_id.setter
    def candidate_id(self, value: str):
        if not value or not str(value).strip():
            raise ValueError("Mã ứng viên không được để trống !")
        self._candidate_id = str(value).strip()

  
    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, value: str):
        val = str(value).strip() if value else ""
        if not val or not DATE_REGEX.match(val):
            raise ValueError(f"Ngày phỏng vấn '{value}' không hợp lệ. Vui lòng nhập đúng định dạng dd/mm/yyyy (vd: 25/10/2026).")
        self._date = val

   
    @property
    def round_name(self):
        return self._round_name

    @round_name.setter
    def round_name(self, value: str):
        if not value or not str(value).strip():
            raise ValueError("Tên vòng phỏng vấn không được để trống !")
        self._round_name = str(value).strip()

  
    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, value: str):
        val = str(value).strip() if value else "Chưa có"
        if val not in VALID_RESULTS:
            raise ValueError(f"Kết quả'{val}' không hợp lệ. Kết quả gồm: {VALID_RESULTS}")
        self._result = val

   
    @property
    def notes(self):
        return self._notes

    @notes.setter
    def notes(self, value: str):
        self._notes = str(value).strip() if value else ""

    def to_dict(self): 
        #giup datamanager luu ds lich phong van xuong file JSON
        return {
            "interview_id": self.interview_id,
            "candidate_id": self.candidate_id,
            "date": self.date,
            "round_name": self.round_name,
            "result": self.result,
            "notes": self.notes
        }
    

    @classmethod
    def from_dict(cls, data: dict):  #khoi tao doi tuong tu dic  
    # doc du lieu tu interviews.json le va chuyen thanh doi tuong python
        return cls(
            interview_id=data["interview_id"],
            candidate_id=data["candidate_id"],
            date=data["date"],
            round_name=data["round_name"],
            result=data.get("result", "Chưa có"),
            notes=data.get("notes", "")
        )