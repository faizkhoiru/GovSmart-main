from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.report import ReportCreate, ReportUpdateStatus, ReportResponse
from app.crud.report import create_report, get_report_by_id, get_reports, update_report_status
from app.api.deps import get_current_user, get_current_active_admin
from app.models.user import User
from app.core.upload import validate_and_save_upload

router = APIRouter()

@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def submit_report(
    report_in: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return create_report(db, report_in, user_id=current_user.id)

@router.get("/", response_model=List[ReportResponse])
def list_reports(
    skip: int = 0,
    limit: int = 100,
    dept_id: Optional[int] = Query(None, description="Filter berdasarkan ID Dinas"),
    status: Optional[str] = Query(None, description="Filter status: diterima, diproses, selesai, ditolak"),
    urgensi: Optional[str] = Query(None, description="Filter urgensi: normal, penting, darurat"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Warga only sees their own reports
    user_id_filter = current_user.id if current_user.role == "warga" else None

    return get_reports(
        db=db,
        skip=skip,
        limit=limit,
        user_id=user_id_filter,
        dept_id=dept_id,
        status=status,
        urgensi=urgensi
    )

@router.get("/{report_id}", response_model=ReportResponse)
def get_report_detail(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan")
    if current_user.role == "warga" and report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Tidak memiliki akses ke laporan ini")
    return report

@router.patch("/{report_id}/status", response_model=ReportResponse)
def change_report_status(
    report_id: int,
    status_in: ReportUpdateStatus,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    report = get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan")

    allowed_statuses = ["diterima", "diproses", "selesai", "ditolak"]
    if status_in.status not in allowed_statuses:
        raise HTTPException(
            status_code=422,
            detail=f"Status tidak valid. Pilihan status yang diperbolehkan: {', '.join(allowed_statuses)}"
        )

    return update_report_status(db, report, status_baru=status_in.status, admin_id=current_admin.id)

@router.post("/{report_id}/upload-foto", response_model=ReportResponse)
def upload_foto_bukti(
    report_id: int,
    foto: UploadFile = File(..., description="Foto bukti kerusakan (JPEG/PNG/WEBP, maks 5 MB)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload foto bukti lampiran untuk sebuah laporan.
    - Hanya pemilik laporan (warga yang membuat) yang boleh mengupload.
    - Tipe file yang diizinkan: JPEG, PNG, WEBP.
    - Ukuran maksimum: 5 MB.
    """
    report = get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan")

    # Hanya pemilik laporan yang boleh upload bukti foto
    if report.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya pemilik laporan yang dapat mengupload foto bukti."
        )

    # Validasi MIME, ekstensi, ukuran, dan simpan file
    saved_filename = validate_and_save_upload(foto)

    # Simpan nama file ke database
    report.foto_bukti = saved_filename
    db.commit()
    db.refresh(report)

    return report
