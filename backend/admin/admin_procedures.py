from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import User, AuditLog, Upload
from schemas import User as UserSchema

def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Get all users with pagination"""
    return db.query(User).offset(skip).limit(limit).all()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()

def activate_user(db: Session, user_id: int) -> bool:
    """Activate a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_active = True
        db.commit()
        return True
    return False

def deactivate_user(db: Session, user_id: int) -> bool:
    """Deactivate a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_active = False
        db.commit()
        return True
    return False

def promote_to_admin(db: Session, user_id: int) -> bool:
    """Promote user to admin"""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_admin = True
        db.commit()
        return True
    return False

def revoke_admin(db: Session, user_id: int) -> bool:
    """Revoke admin privileges"""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_admin = False
        db.commit()
        return True
    return False

def get_system_stats(db: Session) -> dict:
    """Get system statistics"""
    total_users = db.query(func.count(User.id)).scalar()
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
    admin_users = db.query(func.count(User.id)).filter(User.is_admin == True).scalar()
    total_audit_logs = db.query(func.count(AuditLog.id)).scalar()
    total_uploads = db.query(func.count(Upload.id)).scalar()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "admin_users": admin_users,
        "inactive_users": total_users - active_users,
        "total_audit_logs": total_audit_logs,
        "total_uploads": total_uploads
    }

def search_users(
    db: Session,
    query: str,
    skip: int = 0,
    limit: int = 50
) -> List[User]:
    """Search users by username, email, or full name"""
    search_term = f"%{query}%"
    return db.query(User).filter(
        (User.username.ilike(search_term)) |
        (User.email.ilike(search_term)) |
        (User.full_name.ilike(search_term))
    ).offset(skip).limit(limit).all()

def bulk_update_users(db: Session, user_ids: List[int], updates: dict) -> int:
    """Bulk update multiple users"""
    updated_count = db.query(User).filter(
        User.id.in_(user_ids)
    ).update(updates, synchronize_session=False)
    db.commit()
    return updated_count

def delete_user(db: Session, user_id: int) -> bool:
    """Delete a user permanently"""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False