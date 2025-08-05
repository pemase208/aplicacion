from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db import get_database
from dependencies import get_current_active_user
from schemas import User, UserUpdate, Response
from models import User as UserModel

router = APIRouter()

@router.get("/profile", response_model=User)
async def get_my_profile(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Get current user's profile"""
    return current_user

@router.put("/profile", response_model=Response)
async def update_my_profile(
    user_update: UserUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Update current user's profile"""
    try:
        # Update user fields
        if user_update.email is not None:
            # Check if email is already taken by another user
            existing_user = db.query(UserModel).filter(
                UserModel.email == user_update.email,
                UserModel.id != current_user.id
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered by another user"
                )
            current_user.email = user_update.email
        
        if user_update.username is not None:
            # Check if username is already taken by another user
            existing_user = db.query(UserModel).filter(
                UserModel.username == user_update.username,
                UserModel.id != current_user.id
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken by another user"
                )
            current_user.username = user_update.username
        
        if user_update.full_name is not None:
            current_user.full_name = user_update.full_name
        
        # Note: is_active and is_admin are not allowed to be changed by the user themselves
        # These should only be changed by admins
        
        db.commit()
        db.refresh(current_user)
        
        return Response(
            message="Profile updated successfully",
            data={"user_id": current_user.id}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )

@router.get("/settings")
async def get_my_settings(
    current_user: UserModel = Depends(get_current_active_user)
):
    """Get current user's settings"""
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_admin": current_user.is_admin,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at
    }

@router.get("/activity")
async def get_my_activity(
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Get current user's recent activity"""
    from models import AuditLog
    
    # Get recent audit logs for this user
    recent_logs = db.query(AuditLog).filter(
        AuditLog.user_id == current_user.id
    ).order_by(AuditLog.timestamp.desc()).limit(20).all()
    
    return {
        "user_id": current_user.id,
        "recent_activity": [
            {
                "action": log.action,
                "resource": log.resource,
                "timestamp": log.timestamp,
                "details": log.details
            }
            for log in recent_logs
        ]
    }