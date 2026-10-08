from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.user import AdminDinasCreate, AdminDinasUpdate, UserResponse
from app.schemas.audit import AuditLogResponse
from app.crud.user import (
    create_admin_dinas,
    get_user_by_email,
    get_user_by_id,
    get_user_by_nik_or_nip,
    get_user_by_dept_id,
    get_admin_dinas_list,
    update_admin_dinas,
    soft_delete_admin_dinas,
    hard_delete_admin_dinas,
)
from app.crud.department import get_department
from app.crud.report import get_report_by_id
from app.crud.audit import get_audit_logs_by_report
from app.api.deps import get_current_super_admin, get_current_active_admin, get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/me", response_model=UserResponse)
def read_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/admin-dinas", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_admin_dinas_account(
    admin_in: AdminDinasCreate,
    db: Session = Depends(get_db),
    current_super_admin: User = Depends(get_current_super_admin)
):
    if get_user_by_email(db, admin_in.email):
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")
    if get_user_by_nik_or_nip(db, admin_in.nip):
        raise HTTPException(status_code=400, detail="NIP sudah terdaftar")
    if not get_department(db, admin_in.dept_id):
        raise HTTPException(status_code=400, detail="Dinas tidak ditemukan")

    return create_admin_dinas(db, admin_in)

@router.get("/admin-dinas", response_model=List[UserResponse])
def list_admin_dinas(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_super_admin: User = Depends(get_current_super_admin)
):
    admins = get_admin_dinas_list(db, skip=skip, limit=limit)
    return admins

@router.get("/admin-dinas/{admin_id}", response_model=UserResponse)
def get_admin_dinas(
    admin_id: int,
    db: Session = Depends(get_db),
    current_super_admin: User = Depends(get_current_super_admin)
):
    admin = get_user_by_id(db, admin_id)
    if not admin or admin.role != "admin":
        raise HTTPException(status_code=404, detail="Admin Dinas tidak ditemukan")
    setattr(admin, "nama_dinas", get_department(db, admin.dept_id).nama_dinas if admin.dept_id else None)
    return admin

@router.put("/admin-dinas/{admin_id}", response_model=UserResponse)
def edit_admin_dinas(
    admin_id: int,
    admin_in: AdminDinasUpdate,
    db: Session = Depends(get_db),
    current_super_admin: User = Depends(get_current_super_admin)
):
    admin = get_user_by_id(db, admin_id)
    if not admin or admin.role != "admin":
        raise HTTPException(status_code=404, detail="Admin Dinas tidak ditemukan")

    if admin_in.email is not None and get_user_by_email(db, admin_in.email) and get_user_by_email(db, admin_in.email).id != admin.id:
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")
    if admin_in.nip is not None and get_user_by_nik_or_nip(db, admin_in.nip) and get_user_by_nik_or_nip(db, admin_in.nip).id != admin.id:
        raise HTTPException(status_code=400, detail="NIP sudah terdaftar")
    if admin_in.dept_id is not None and not get_department(db, admin_in.dept_id):
        raise HTTPException(status_code=400, detail="Dinas tidak ditemukan")

    result = update_admin_dinas(db, admin_id, admin_in)
    if not result:
        raise HTTPException(status_code=404, detail="Admin Dinas tidak ditemukan")
    return result

@router.delete("/admin-dinas/{admin_id}", response_model=UserResponse)
def delete_admin_dinas(
    admin_id: int,
    hard: Optional[bool] = False,
    db: Session = Depends(get_db),
    current_super_admin: User = Depends(get_current_super_admin)
):
    admin = get_user_by_id(db, admin_id)
    if not admin or admin.role != "admin":
        raise HTTPException(status_code=404, detail="Admin Dinas tidak ditemukan")

    if hard:
        hard_delete_admin_dinas(db, admin_id)
    else:
        soft_delete_admin_dinas(db, admin_id)
    return admin

@router.get("/audit-logs/{report_id}", response_model=List[AuditLogResponse])
def get_report_audit_history(
    report_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    report = get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan")
    if current_admin.role == "admin" and report.dept_id != current_admin.dept_id:
        raise HTTPException(status_code=403, detail="Tidak memiliki akses ke laporan ini")
    return get_audit_logs_by_report(db, report_id=report_id)
