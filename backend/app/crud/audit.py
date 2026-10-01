from sqlalchemy.orm import Session
from app.models.audit import AuditLog

def create_audit_log(db: Session, report_id: int, admin_id: int, status_baru: str):
    log_entry = AuditLog(
        report_id=report_id,
        admin_id=admin_id,
        status_baru=status_baru
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry

def get_audit_logs_by_report(db: Session, report_id: int):
    return db.query(AuditLog).filter(AuditLog.report_id == report_id).order_by(AuditLog.timestamp.desc()).all()
