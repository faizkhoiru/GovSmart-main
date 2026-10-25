from sqlalchemy.orm import Session
from sqlalchemy import case
from typing import Optional, List, cast
from app.models.report import Report
from app.schemas.report import ReportCreate, ReportUpdate
from app.core.ai_routing import analyze_report_ai
from app.crud.audit import create_audit_log

def create_report(db: Session, report_in: ReportCreate, user_id: int):
    # Run AI smart routing and urgency analysis
    ai_dept_id, ai_urgensi = analyze_report_ai(report_in.judul, report_in.isi_laporan, db)

    # Use manual dept_id if supplied, otherwise fallback to AI suggestion
    final_dept_id = report_in.dept_id if report_in.dept_id else ai_dept_id

    db_report = Report(
        user_id=user_id,
        dept_id=final_dept_id,
        judul=report_in.judul,
        isi_laporan=report_in.isi_laporan,
        status="diterima",
        urgensi=ai_urgensi,
        lat=report_in.lat,
        long=report_in.long
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    # Audit trail: record the initial 'diterima' (received) status from the system/AI.
    create_audit_log(db, report_id=cast(int, db_report.id), admin_id=None, status_baru="diterima")

    return db_report

def get_report_by_id(db: Session, report_id: int):
    return db.query(Report).filter(Report.id == report_id).first()


def update_report(db: Session, report: Report, report_in: ReportUpdate):
    ai_dept_id, ai_urgensi = analyze_report_ai(report_in.judul, report_in.isi_laporan, db)
    report.judul = report_in.judul
    report.isi_laporan = report_in.isi_laporan
    report.dept_id = report_in.dept_id or ai_dept_id
    report.urgensi = ai_urgensi
    report.lat = report_in.lat
    report.long = report_in.long
    db.commit()
    db.refresh(report)
    return report


def cancel_report(db: Session, report: Report):
    report.status = "dibatalkan"
    db.commit()
    db.refresh(report)
    create_audit_log(db, report_id=cast(int, report.id), admin_id=None, status_baru="dibatalkan")
    return report


MAKE_REPORT_HISTORY_LIMIT = 5


def get_report_history(db: Session, user_id: int):
    return (
        db.query(Report)
        .filter(Report.user_id == user_id)
        .order_by(Report.id.desc())
        .limit(MAKE_REPORT_HISTORY_LIMIT)
        .all()
    )


def get_reports(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    dept_id: Optional[int] = None,
    status: Optional[str] = None,
    urgensi: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Report]:
    from datetime import datetime
    query = db.query(Report)

    if user_id:
        query = query.filter(Report.user_id == user_id)
    if dept_id:
        query = query.filter(Report.dept_id == dept_id)
    if status:
        query = query.filter(Report.status == status)
    if urgensi:
        query = query.filter(Report.urgensi == urgensi)
    if start_date:
        try:
            sd = datetime.fromisoformat(start_date)
            query = query.filter(Report.created_at >= sd)
        except ValueError:
            pass
    if end_date:
        try:
            ed = datetime.fromisoformat(end_date)
            query = query.filter(Report.created_at <= ed)
        except ValueError:
            pass

    # Sort urgency: 'darurat' first (1), 'penting' second (2), 'normal' third (3)
    urgency_order = case(
        (Report.urgensi == 'darurat', 1),
        (Report.urgensi == 'penting', 2),
        else_=3
    )

    return query.order_by(urgency_order, Report.id.desc()).offset(skip).limit(limit).all()

def update_report_status(db: Session, report: Report, status_baru: str, admin_id: int, catatan_petugas: Optional[str] = None):
    setattr(report, "status", status_baru)
    if catatan_petugas is not None:
        setattr(report, "catatan_petugas", catatan_petugas.strip() or None)
    db.commit()
    db.refresh(report)

    # Record audit log automatically
    create_audit_log(db, report_id=cast(int, report.id), admin_id=admin_id, status_baru=status_baru)
    return report
