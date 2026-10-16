from models.person import Person 
VALID_STAGES = ["Ứng tuyển", "Sơ tuyển", "Phỏng vấn", "Kết quả"]

class Candidate(Person):
    def __init__(self, person_id: str, full_name:str, email:str, phone:str, job_id: str, source:str = "Website Cong ty", stage:str ="Ung tuyen"):
        super().__init__(person_id, full_name, email, phone)
        self._job_id = ""
        self._source = ""
        self._stage = ""

        self.job_id = job_id  #ma vi tri cong viec 
        self.source = source  #nguon ung vien
        self.stage = stage    #vong tuyen dung

    @property 
    def job_id(self):
        return self._job_id 
        
    @job_id.setter
    def job_id(self, value: str):
        if not value or not str(value).strip():
            raise ValueError("Mã vị trí công việc không được để trống !")
        self._job_id = str(value).strip()
    
    @property 
    def source(self):
        return self._source
    
    @source.setter
    def source(self, value: str):
        val = str(value).strip() if value else ""
        if not val:
            self._source = "Nguồn khác"
        else:
            self._source = val 


    @property 
    def stage(self):
        return self._stage 
    
    @stage.setter
    def stage(self, value: str):
        val = str(value).strip() if value else ""
        if not val:
            raise ValueError("Trạng thái không được để trống!")
        if val not in VALID_STAGES:
            raise ValueError(f"Trạng thái '{val}' không hợp lệ !") 
        self._stage = val    
    

    def get_role_display(self):
        return "Ứng viên"


    def to_dict(self): #chuyen toan bo du lieu thanh dictionary
        return {
            "person_id": self.person_id,
            "full_name": self.full_name,
            "email": self.email,
            "phone":self.phone,
            "job_id": self.job_id,
            "source":self.source,
            "stage": self.stage
        }


    @classmethod
    def from_dict(cls, data: dict): 
    #doc du lieu tu dang dict tu file JSON va khoi tao lai doi tuong
        return cls(
            person_id=data["person_id"],
            full_name=data["full_name"],
            email=data["email"],
            phone=data["phone"],
            job_id=data.get("job_id", ""),
            source=data.get("source", "Website cong ty"),
            stage=data.get("stage", "Ung tuyen")
        )

