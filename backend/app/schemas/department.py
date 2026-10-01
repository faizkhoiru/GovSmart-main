from pydantic import BaseModel, Field

class DepartmentBase(BaseModel):
    nama_dinas: str = Field(..., min_length=3, max_length=100)

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentResponse(DepartmentBase):
    id: int

    class Config:
        from_attributes = True
