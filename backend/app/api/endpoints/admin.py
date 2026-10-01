from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.user import AdminDinasCreate, UserResponse
from app.schemas.audit import AuditLogResponse
from app.crud.user import create_admin_dinas, get_user_by_email, get_user_by_nik_or_nip
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

    return create_admin_dinas(db, admin_in)

@router.get("/audit-logs/{report_id}", response_model=List[AuditLogResponse])
def get_report_audit_history(
    report_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    return get_audit_logs_by_report(db, report_id=report_id)
