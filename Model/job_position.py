
VALID_STATUSES  = ["Dang tuyen", "Tam dung", "Da dong"]

class JobPosting: # class doc lap danh cho tin tuyen dung
    def __init__(self, job_id: str, title:str, department: str, min_salary: float,
            max_salary: float, quota: int, requirements:str):
        self._job_id = ""
        self._title = ""
        self._department = ""
        self._min_salary = 0.0
        self._max_salary = 0.0
        self._quota = 1
        self._requirements = ""

        self.job_id = job_id
        self.title = title  #ten  vi tri cong viec
        self.min_salary = min_salary
        self.max_salary = max_salary
        self.quota = quota
        self.department = department
        self.requirements = requirements #yeu cau cong viec

    @property 
    def job_id(self):
        return self._job_id 
            
    @job_id.setter
    def job_id(self, value: str):
        if not value or not str(value).strip():
            raise ValueError("Mã vị trí công việc không được để trống !")
        self._job_id = str(value).strip()

    @property 
    def title(self):
        return self._title

    @title.setter
    def title(self, value: str):
        if not value or not str(value).strip():
            raise ValueError("Tên vị trí công việc không được để trống !")
        self._title = str(value).strip()

    @property 
    def department(self):
        return self._department

    @department.setter
    def department(self, value: str):
        if not value or not str(value).strip():
            raise ValueError("Tên phòng ban không được để trống !")
        self._department = str(value).strip()

    @property
    def min_salary(self) -> float:
        return self._min_salary
    
    @min_salary.setter
    def min_salary(self, value: float):
        try:
            val = float(value)
        except (ValueError, TypeError):
            raise ValueError("Mức lương tối thiểu phải là số. ")
        if val < 0:
            raise ValueError("Mức lương tối thiểu không được âm. ")
        if self._max_salary > 0 and val > self._max_salary:
            raise ValueError(f"Mức lương tối thiểu ({val}) không được lớn hơn lương tối đa ({self._max_salary}).")
        self._min_salary = val
    
        @property
        def max_salary(self) -> float:
            return self._max_salary
    
        @max_salary.setter
        def max_salary(self, value: float):
            try:
                val = float(value)
            except (ValueError, TypeError):
                raise ValueError("Mức lương tối đa phải là số. ")
            if val < 0:
                raise ValueError("Mức lương tối đa không được âm.")
            if val < self._min_salary:
                raise ValueError(f"Mức lương tối đa ({val}) không được nhỏ hơn lương tối thiểu ({self._min_salary}).")
            self._max_salary = val
    
     
        @property
        def quota(self):
            return self._quota
    
        @quota.setter
        def quota(self, value: int):
            try:
                if isinstance(value, bool) or str(value).strip() != str(int(value)):
                    raise ValueError
                val = int(value)
            except (ValueError, TypeError):
                raise ValueError("Chỉ tiêu tuyển dụng (quota) phải là số nguyên.")
            if val <= 0:
                raise ValueError(f"Chỉ tiêu tuyển dụng phải là số nguyên dương > 0 (nhận được: {value}).")
            self._quota = val


    @property
    def requirements(self):
        return self._requirements

    @requirements.setter
    def requirements(self, value: str):
        if not value or not str(value).strip():
            raise ValueError("Yêu cầu công việc không được để trống.")
        self._requirements = str(value).strip()

    def to_dict(self): #chuyen thanh dictionary giup datamanager de quan ly 
        return {
            "job_id": self.job_id,
            "title": self.title,
            "department": self.department,
            "requirements": self.requirements
        }

    @classmethod #phuong thuc lop -> goi truc tiep qua JobPosting.from_dict(data) de tao doi tuong 
    def from_dict(cls, data:dict):
        return cls(
            job_id = data["job_id"],
            title = data["title"],
            department = data["department"], 
            requirements = data["requirements"]
        )

