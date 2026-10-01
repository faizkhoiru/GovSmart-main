from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.department import DepartmentCreate, DepartmentResponse
from app.crud.department import get_departments, create_department, get_department_by_name
from app.api.deps import get_current_super_admin
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[DepartmentResponse])
def read_departments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_departments(db, skip=skip, limit=limit)

@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def add_department(
    dept_in: DepartmentCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_super_admin)
):
    existing = get_department_by_name(db, dept_in.nama_dinas)
    if existing:
        raise HTTPException(status_code=400, detail="Nama dinas sudah terdaftar")
    return create_department(db, dept_in)
