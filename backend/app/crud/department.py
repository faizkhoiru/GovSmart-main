from sqlalchemy.orm import Session
from app.models.department import Department
from app.schemas.department import DepartmentCreate
from app.core.ai_routing import DEFAULT_DEPARTMENTS

def get_department(db: Session, dept_id: int):
    return db.query(Department).filter(Department.id == dept_id).first()

def get_department_by_name(db: Session, nama_dinas: str):
    return db.query(Department).filter(Department.nama_dinas == nama_dinas).first()

def get_departments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Department).offset(skip).limit(limit).all()

def create_department(db: Session, dept: DepartmentCreate):
    db_dept = Department(nama_dinas=dept.nama_dinas)
    db.add(db_dept)
    db.commit()
    db.refresh(db_dept)
    return db_dept

def seed_departments(db: Session):
    for dept_name in DEFAULT_DEPARTMENTS:
        existing = get_department_by_name(db, dept_name)
        if not existing:
            db_dept = Department(nama_dinas=dept_name)
            db.add(db_dept)
    db.commit()
