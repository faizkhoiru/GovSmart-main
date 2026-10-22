from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy import desc
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.report import ReportCreate, ReportUpdateStatus, ReportResponse
from app.crud.report import create_report, get_report_by_id, get_reports, update_report_status
from app.api.deps import get_current_user, get_current_active_admin
from app.models.user import User
from app.models.report import Report
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
    # Warga only sees their own reports. Admin dinas only sees reports routed to their dinas.
    user_id_filter = current_user.id if current_user.role == "warga" else None
    dept_id_filter = current_user.dept_id if current_user.role == "admin" else dept_id

    return get_reports(
        db=db,
        skip=skip,
        limit=limit,
        user_id=user_id_filter,
        dept_id=dept_id_filter,
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
    if current_user.role == "admin" and report.dept_id != current_user.dept_id:
        raise HTTPException(status_code=403, detail="Tidak memiliki akses ke laporan ini")
    return report

@router.get("/notifications/me", response_model=List[ReportResponse])
def get_my_notifications(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin),
):
    """
    Notifikasi laporan baru untuk admin dinas.
    Kembalikan (limit) laporan yang dialokasikan ke dinas admin ini dengan status
    'diterima' atau 'diproses' (belum selesai/ditolak), urut terbaru dulu.
    """
    pendidng = (
        db.query(Report)
        .filter(
            Report.dept_id == current_user.dept_id,
            Report.status.in_(["diterima", "diproses"]),
        )
        .order_by(desc(Report.created_at))
        .limit(limit)
        .all()
    )
    return pendidng

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
    if current_admin.role == "admin" and report.dept_id != current_admin.dept_id:
        raise HTTPException(status_code=403, detail="Tidak memiliki akses ke laporan ini")

    allowed_statuses = ["diterima", "diproses", "selesai", "ditolak"]
    if status_in.status not in allowed_statuses:
        raise HTTPException(
            status_code=422,
            detail=f"Status tidak valid. Pilihan status yang diperbolehkan: {', '.join(allowed_statuses)}"
        )

    return update_report_status(
        db,
        report,
        status_baru=status_in.status,
        admin_id=current_admin.id,
        catatan_petugas=status_in.catatan_petugas
    )

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
    setattr(report, "foto_bukti", saved_filename)
    db.commit()
    db.refresh(report)

    return report

@router.post("/sync-routing")
def sync_unrouted_reports(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """
    Menyelaraskan semua laporan yang belum ter-routing secara otomatis (dept_id is NULL)
    menggunakan model AI smart routing terbaru.
    """
    from app.core.ai_routing import analyze_report_ai

    unrouted = db.query(Report).filter(Report.dept_id == None).all()
    updated_count = 0
    details = []

    for rep in unrouted:
        dept_id, urgensi = analyze_report_ai(rep.judul, rep.isi_laporan, db)
        setattr(rep, "dept_id", dept_id)
        if urgensi:
            setattr(rep, "urgensi", urgensi)
        updated_count += 1
        details.append({"report_id": rep.id, "judul": rep.judul, "dept_id": dept_id, "urgensi": urgensi})

    if updated_count > 0:
        db.commit()

    return {
        "status": "success",
        "total_unrouted_found": len(unrouted),
        "total_updated": updated_count,
        "details": details
    }

@router.post("/{report_id}/reroute", response_model=ReportResponse)
def reroute_single_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """
    Menganalisis ulang dan me-reroute laporan secara otomatis menggunakan AI smart routing.
    """
    from app.core.ai_routing import analyze_report_ai

    report = get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan")

    dept_id, urgensi = analyze_report_ai(report.judul, report.isi_laporan, db)
    setattr(report, "dept_id", dept_id)
    if urgensi:
        setattr(report, "urgensi", urgensi)

    db.commit()
    db.refresh(report)
    return report
