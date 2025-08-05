from typing import Optional
from sqlalchemy.orm import Session
from models import AuditLog

async def log_audit_event(
    db: Session,
    user_id: Optional[int],
    action: str,
    resource: Optional[str] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """Log an audit event to the database"""
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    db.add(audit_log)
    db.commit()
    return audit_log

def get_user_audit_logs(db: Session, user_id: int, limit: int = 50):
    """Get audit logs for a specific user"""
    return db.query(AuditLog).filter(
        AuditLog.user_id == user_id
    ).order_by(AuditLog.timestamp.desc()).limit(limit).all()

def get_all_audit_logs(db: Session, limit: int = 100):
    """Get all audit logs (admin only)"""
    return db.query(AuditLog).order_by(
        AuditLog.timestamp.desc()
    ).limit(limit).all()

def get_audit_logs_by_action(db: Session, action: str, limit: int = 50):
    """Get audit logs filtered by action"""
    return db.query(AuditLog).filter(
        AuditLog.action == action
    ).order_by(AuditLog.timestamp.desc()).limit(limit).all()