from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.user import (
    AdminDinasCreate,
    AdminDinasUpdate,
    WargaAdminUpdate,
    UserProfileUpdate,
    UserProfileUpdateResponse,
    UserResponse,
)
from app.core.security import get_password_hash, create_access_token
from app.schemas.audit import AuditLogResponse
from app.crud.user import (
    create_admin_dinas,
    get_user_by_email,
    get_user_by_id,
    get_user_by_nik_or_nip,
    get_user_by_dept_id,
    get_admin_dinas_list,
    update_admin_dinas,
    activate_admin_dinas,
    soft_delete_admin_dinas,
    hard_delete_admin_dinas,
    get_warga_list,
    update_warga_user,
    soft_delete_warga_user,
    activate_warga_user,
    hard_delete_warga_user,
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


@router.put("/me", response_model=UserProfileUpdateResponse)
def update_current_user_profile(
    profile_in: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Memperbarui profil pengguna yang sedang login (nama lengkap, email, no. telepon, alamat,
    dan password baru opsional). NIK/NIP tidak dapat diubah demi integritas identitas.
    """
    email_changed = False
    if profile_in.email is not None:
        new_email = str(profile_in.email).strip().lower()
        if new_email != current_user.email:
            existing = get_user_by_email(db, new_email)
            if existing and existing.id != current_user.id:
                raise HTTPException(status_code=400, detail="Email sudah digunakan oleh akun lain")
            current_user.email = new_email
            email_changed = True

    if profile_in.nama_lengkap is not None:
        cleaned = profile_in.nama_lengkap.strip()
        current_user.nama_lengkap = cleaned if cleaned else None

    if profile_in.no_telepon is not None:
        cleaned = profile_in.no_telepon.strip()
        current_user.no_telepon = cleaned if cleaned else None

    if profile_in.alamat is not None:
        cleaned = profile_in.alamat.strip()
        current_user.alamat = cleaned if cleaned else None

    if profile_in.password:
        current_user.password_hash = get_password_hash(profile_in.password)

    db.commit()
    db.refresh(current_user)

    new_token = create_access_token(subject=current_user.email) if email_changed else None
    dept = get_department(db, current_user.dept_id) if current_user.dept_id else None
    return UserProfileUpdateResponse(
        id=current_user.id,
        nik_or_nip=current_user.nik_or_nip,
        email=current_user.email,
        role=current_user.role,
        dept_id=current_user.dept_id,
        is_active=current_user.is_active,
        nama_dinas=dept.nama_dinas if dept else None,
        nama_lengkap=current_user.nama_lengkap,
        no_telepon=current_user.no_telepon,
        alamat=current_user.alamat,
        access_token=new_token,
    )

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
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_super_admin: User = Depends(get_current_super_admin)
):
    admins = get_admin_dinas_list(db, skip=skip, limit=limit, include_inactive=include_inactive)
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

@router.post("/admin-dinas/{admin_id}/activate", response_model=UserResponse)
def reactivate_admin_dinas(
    admin_id: int,
    db: Session = Depends(get_db),
    current_super_admin: User = Depends(get_current_super_admin)
):
    admin = activate_admin_dinas(db, admin_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Admin Dinas tidak ditemukan")
    return admin


@router.get("/warga", response_model=List[UserResponse])
def list_warga_users(
    skip: int = 0,
    limit: int = 200,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_super_admin: User = Depends(get_current_super_admin),
):
    return get_warga_list(db, skip=skip, limit=limit, include_inactive=include_inactive)


@router.put("/warga/{user_id}", response_model=UserResponse)
def edit_warga_user(
    user_id: int,
    warga_in: WargaAdminUpdate,
    db: Session = Depends(get_db),
    current_super_admin: User = Depends(get_current_super_admin),
):
    warga = get_user_by_id(db, user_id)
    if not warga or warga.role != "warga":
        raise HTTPException(status_code=404, detail="Akun warga tidak ditemukan")
    if warga_in.email is not None:
        new_email = str(warga_in.email).strip().lower()
        existing = get_user_by_email(db, new_email)
        if existing and existing.id != warga.id:
            raise HTTPException(status_code=400, detail="Email sudah digunakan oleh akun lain")
    updated = update_warga_user(db, user_id, warga_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Akun warga tidak ditemukan")
    return updated


@router.delete("/warga/{user_id}", response_model=UserResponse)
def delete_warga_user(
    user_id: int,
    hard: Optional[bool] = False,
    db: Session = Depends(get_db),
    current_super_admin: User = Depends(get_current_super_admin),
):
    warga = get_user_by_id(db, user_id)
    if not warga or warga.role != "warga":
        raise HTTPException(status_code=404, detail="Akun warga tidak ditemukan")
    if hard:
        hard_delete_warga_user(db, user_id)
    else:
        soft_delete_warga_user(db, user_id)
    return warga


@router.post("/warga/{user_id}/activate", response_model=UserResponse)
def reactivate_warga_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_super_admin: User = Depends(get_current_super_admin),
):
    warga = activate_warga_user(db, user_id)
    if not warga:
        raise HTTPException(status_code=404, detail="Akun warga tidak ditemukan")
    return warga

@router.get("/audit-logs/{report_id}", response_model=List[AuditLogResponse])
def get_report_audit_history(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan")
    if current_user.role == "warga" and report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Tidak memiliki akses ke riwayat laporan ini")
    if current_user.role == "admin" and report.dept_id != current_user.dept_id:
        raise HTTPException(status_code=403, detail="Tidak memiliki akses ke laporan ini")
    return get_audit_logs_by_report(db, report_id=report_id)
