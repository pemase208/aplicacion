from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from db import get_db
from models import User
from schemas import User as UserSchema, UserUpdate, Message, AuditLog as AuditLogSchema
from dependencies import get_current_active_user, get_client_ip, get_user_agent
from audit import log_audit_event, get_user_audit_logs

router = APIRouter()

@router.get("/profile", response_model=UserSchema)
async def get_my_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user's profile"""
    return current_user

@router.put("/profile", response_model=UserSchema)
async def update_my_profile(
    user_update: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    update_data = user_update.dict(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    # Check if username or email already exists (if being updated)
    if "username" in update_data:
        existing_user = db.query(User).filter(
            User.username == update_data["username"],
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    if "email" in update_data:
        existing_user = db.query(User).filter(
            User.email == update_data["email"],
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken"
            )
    
    # Update user
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    # Log profile update
    await log_audit_event(
        db=db,
        user_id=current_user.id,
        action="profile_updated",
        resource="user_profile",
        details=f"Updated fields: {', '.join(update_data.keys())}",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    return current_user

@router.get("/audit-logs")
async def get_my_audit_logs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's audit logs"""
    logs = get_user_audit_logs(db, current_user.id)
    return logs

@router.delete("/profile", response_model=Message)
async def deactivate_my_account(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Deactivate current user's account"""
    current_user.is_active = False
    db.commit()
    
    # Log account deactivation
    await log_audit_event(
        db=db,
        user_id=current_user.id,
        action="account_deactivated",
        resource="user_profile",
        details="User deactivated their own account",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    return {"message": "Account deactivated successfully"}