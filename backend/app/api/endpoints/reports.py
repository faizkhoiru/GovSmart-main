from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy import desc
from sqlalchemy.orm import Session
from typing import List, Optional, cast
from app.database import get_db
from app.schemas.report import ReportCreate, ReportUpdate, ReportUpdateStatus, ReportResponse
from app.crud.report import (
    create_report,
    get_report_by_id,
    get_reports,
    get_report_history,
    update_report,
    cancel_report,
    update_report_status,
)
from app.api.deps import get_current_user, get_current_active_admin
from app.models.user import User
from app.models.report import Report
from app.crud.department import get_department
from app.core.upload import validate_and_save_upload, IMAGE_MIME_TYPES, IMAGE_EXTENSIONS, FEEDBACK_MIME_TYPES, FEEDBACK_EXTENSIONS

router = APIRouter()

@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def submit_report(
    report_in: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if report_in.dept_id is not None and not get_department(db, report_in.dept_id):
        raise HTTPException(status_code=422, detail="Dinas tujuan tidak ditemukan")
    return create_report(db, report_in, user_id=cast(int, current_user.id))

@router.get("/", response_model=List[ReportResponse])
def list_reports(
    skip: int = 0,
    limit: int = 100,
    dept_id: Optional[int] = Query(None, description="Filter berdasarkan ID Dinas"),
    status: Optional[str] = Query(None, description="Filter status: diterima, diproses, selesai, ditolak"),
    urgensi: Optional[str] = Query(None, description="Filter urgensi: normal, penting, darurat"),
    start_date: Optional[str] = Query(None, description="Filter dari tanggal (ISO format: YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter sampai tanggal (ISO format: YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Warga only sees their own reports. Admin dinas only sees reports routed to their dinas.
    user_id_filter = current_user.id if current_user.role == "warga" else None
    dept_id_filter = current_user.dept_id if current_user.role == "admin" else dept_id
    if current_user.role == "warga":
        limit = min(limit, 5)

    return get_reports(
        db=db,
        skip=skip,
        limit=limit,
        user_id=user_id_filter,
        dept_id=dept_id_filter,
        status=status,
        urgensi=urgensi,
        start_date=start_date,
        end_date=end_date
    )

@router.get("/history", response_model=List[ReportResponse])
def my_report_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_report_history(db, cast(int, current_user.id))


@router.put("/{report_id}", response_model=ReportResponse)
def edit_my_report(
    report_id: int,
    report_in: ReportUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan")
    if current_user.role != "warga" or report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Hanya pemilik laporan yang dapat mengedit laporan")
    if report.status != "diterima":
        raise HTTPException(status_code=409, detail="Laporan hanya dapat diedit sebelum diproses")
    if report_in.dept_id is not None and not get_department(db, report_in.dept_id):
        raise HTTPException(status_code=422, detail="Dinas tujuan tidak ditemukan")
    return update_report(db, report, report_in)


@router.post("/{report_id}/cancel", response_model=ReportResponse)
def cancel_my_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan")
    if current_user.role != "warga" or report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Hanya pemilik laporan yang dapat membatalkan laporan")
    if report.status != "diterima":
        raise HTTPException(status_code=409, detail="Laporan hanya dapat dibatalkan sebelum diproses")
    return cancel_report(db, report)


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
        .order_by(desc(Report.id))
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
        admin_id=cast(int, current_admin.id),
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

    # Validasi MIME, ekstensi, ukuran, dan simpan file (hanya gambar untuk bukti)
    saved_filename = validate_and_save_upload(
        foto,
        allowed_mime_types=IMAGE_MIME_TYPES,
        allowed_extensions=IMAGE_EXTENSIONS,
        allowed_label="JPEG, PNG, WEBP",
    )

    # Simpan nama file ke database
    setattr(report, "foto_bukti", saved_filename)
    db.commit()
    db.refresh(report)

    return report

@router.post("/{report_id}/upload-feedback", response_model=ReportResponse)
def upload_foto_feedback(
    report_id: int,
    foto: UploadFile = File(..., description="Dokumen/foto feedback dari admin dinas (JPEG/PNG/WEBP/PDF, maks 5 MB)"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    """
    Upload dokumen/foto sebagai feedback/bukti dukung dari admin dinas
    terhadap laporan pengguna.
    - Hanya admin dinas yang bertugas (report.dept_id == current_admin.dept_id) yang boleh.
    - Tipe file: JPEG, PNG, WEBP, PDF. Ukuran maksimum: 5 MB.
    """
    report = get_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan")
    if report.dept_id != current_admin.dept_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya admin dinas yang bertugas pada laporan ini yang dapat mengupload feedback."
        )
    saved_filename = validate_and_save_upload(
        foto,
        allowed_mime_types=FEEDBACK_MIME_TYPES,
        allowed_extensions=FEEDBACK_EXTENSIONS,
        allowed_label="JPEG, PNG, WEBP, PDF",
    )
    setattr(report, "foto_feedback", saved_filename)
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
        dept_id, urgensi = analyze_report_ai(cast(str, rep.judul), cast(str, rep.isi_laporan), db)
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

    dept_id, urgensi = analyze_report_ai(cast(str, report.judul), cast(str, report.isi_laporan), db)
    setattr(report, "dept_id", dept_id)
    if urgensi:
        setattr(report, "urgensi", urgensi)

    db.commit()
    db.refresh(report)
    return report


@router.get("/export/csv")
def export_reports_csv(
    dept_id: Optional[int] = Query(None, description="Filter berdasarkan ID Dinas"),
    status: Optional[str] = Query(None, description="Filter status"),
    urgensi: Optional[str] = Query(None, description="Filter urgensi"),
    start_date: Optional[str] = Query(None, description="Filter dari tanggal (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter sampai tanggal (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export laporan yang sudah difilter ke format CSV.
    Hanya bisa diakses oleh admin, admin dinas, atau super admin.
    """
    if current_user.role not in ("admin", "admin_dinas", "super_admin"):
        raise HTTPException(status_code=403, detail="Tidak memiliki akses untuk mengekspor laporan")

    # super_admin & admin bisa lihat semua dinas; admin_dinas hanya dinasnya sendiri
    if current_user.role == "admin_dinas":
        dept_filter = current_user.dept_id
    elif dept_id is not None:
        dept_filter = dept_id
    else:
        dept_filter = None

    reports = get_reports(
        db=db,
        skip=0,
        limit=10000,
        dept_id=dept_filter,
        status=status,
        urgensi=urgensi,
        start_date=start_date,
        end_date=end_date
    )

    import csv
    import io
    from datetime import datetime

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Judul", "Isi Laporan", "Urgensi", "Dinas", "Status", "Lokasi Lat", "Lokasi Long", "Catatan Petugas", "Tanggal Dibuat", "Nama Pengguna"])
    user_cache = {}
    for r in reports:
        dept = get_department(db, cast(int, r.dept_id)) if r.dept_id else None
        dept_name = dept.nama_dinas if dept else "Auto-Routing"
        if r.user_id not in user_cache:
            u = db.query(User).filter(User.id == r.user_id).first()
            user_cache[r.user_id] = u.email if u else f"User #{r.user_id}"
        user_label = user_cache[r.user_id]
        created_val = getattr(r, "created_at", None)
        created_str = created_val.strftime("%Y-%m-%d %H:%M:%S") if created_val else ""
        writer.writerow([
            r.id,
            r.judul,
            r.isi_laporan,
            r.urgensi,
            dept_name,
            r.status,
            r.lat or "",
            r.long or "",
            r.catatan_petugas or "",
            created_str,
            user_label
        ])

    response = output.getvalue().encode("utf-8-sig")
    from fastapi.responses import Response as FastAPIResponse
    return FastAPIResponse(
        content=response,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=govsmart_laporan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )


@router.get("/export/html")
def export_reports_html(
    dept_id: Optional[int] = Query(None, description="Filter berdasarkan ID Dinas"),
    status: Optional[str] = Query(None, description="Filter status"),
    urgensi: Optional[str] = Query(None, description="Filter urgensi"),
    start_date: Optional[str] = Query(None, description="Filter dari tanggal (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter sampai tanggal (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export laporan yang sudah difilter ke format HTML (bisa dicetak ke PDF via browser).
    Hanya bisa diakses oleh admin, admin dinas, atau super admin.
    """
    if current_user.role not in ("admin", "admin_dinas", "super_admin"):
        raise HTTPException(status_code=403, detail="Tidak memiliki akses untuk mengekspor laporan")

    # super_admin & admin bisa lihat semua dinas; admin_dinas hanya dinasnya sendiri
    if current_user.role == "admin_dinas":
        dept_filter = current_user.dept_id
    elif dept_id is not None:
        dept_filter = dept_id
    else:
        dept_filter = None

    reports = get_reports(
        db=db,
        skip=0,
        limit=10000,
        dept_id=dept_filter,
        status=status,
        urgensi=urgensi,
        start_date=start_date,
        end_date=end_date
    )

    from fastapi.responses import HTMLResponse
    from datetime import datetime

    rows_html = ""
    for r in reports:
        dept = get_department(db, cast(int, r.dept_id)) if r.dept_id else None
        dept_name = dept.nama_dinas if dept else "Auto-Routing"
        created_val = getattr(r, "created_at", None)
        created = created_val.strftime("%d/%m/%Y %H:%M") if created_val else "-"
        rows_html += f"""
        <tr>
            <td>{r.id}</td>
            <td>{r.judul}</td>
            <td>{r.urgensi}</td>
            <td>{dept_name}</td>
            <td>{r.status}</td>
            <td>{r.lat or ''}, {r.long or ''}</td>
            <td>{r.catatan_petugas or '-'}</td>
            <td>{created}</td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Laporan GovSmart - {datetime.now().strftime('%d/%m/%Y %H:%M')}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #1e3a8a; border-bottom: 2px solid #1e3a8a; padding-bottom: 10px; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #1e3a8a; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            .export-info {{ color: #666; font-size: 0.9em; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <h1>Laporan GovSmart</h1>
        <p class="export-info">Dicetak pada: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        <p class="export-info">Total laporan: {len(reports)}</p>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Judul</th>
                    <th>Urgensi</th>
                    <th>Dinas</th>
                    <th>Status</th>
                    <th>Lokasi</th>
                    <th>Catatan Petugas</th>
                    <th>Tanggal</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
