from sqlalchemy.orm import Session
from sqlalchemy import case
from typing import Optional, List
from app.models.report import Report
from app.schemas.report import ReportCreate
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
    return db_report

def get_report_by_id(db: Session, report_id: int):
    return db.query(Report).filter(Report.id == report_id).first()

def get_reports(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    dept_id: Optional[int] = None,
    status: Optional[str] = None,
    urgensi: Optional[str] = None
) -> List[Report]:
    query = db.query(Report)

    if user_id:
        query = query.filter(Report.user_id == user_id)
    if dept_id:
        query = query.filter(Report.dept_id == dept_id)
    if status:
        query = query.filter(Report.status == status)
    if urgensi:
        query = query.filter(Report.urgensi == urgensi)

    # Sort urgency: 'darurat' first (1), 'penting' second (2), 'normal' third (3)
    urgency_order = case(
        (Report.urgensi == 'darurat', 1),
        (Report.urgensi == 'penting', 2),
        else_=3
    )

    return query.order_by(urgency_order, Report.id.desc()).offset(skip).limit(limit).all()

def update_report_status(db: Session, report: Report, status_baru: str, admin_id: int):
    report.status = status_baru
    db.commit()
    db.refresh(report)

    # Record audit log automatically
    create_audit_log(db, report_id=report.id, admin_id=admin_id, status_baru=status_baru)
    return report
