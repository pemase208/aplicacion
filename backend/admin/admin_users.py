from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from db import get_db
from models import User
from schemas import User as UserSchema, UserUpdate, Message, SuccessResponse
from dependencies import get_current_admin_user, get_client_ip, get_user_agent
from audit import log_audit_event
from admin.admin_procedures import (
    get_all_users,
    get_user_by_id,
    activate_user,
    deactivate_user,
    promote_to_admin,
    revoke_admin,
    get_system_stats,
    search_users,
    bulk_update_users,
    delete_user
)

router = APIRouter()

@router.get("/users", response_model=List[UserSchema])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List all users with optional search"""
    if search:
        users = search_users(db, search, skip, limit)
    else:
        users = get_all_users(db, skip, limit)
    
    return users

@router.get("/users/{user_id}", response_model=UserSchema)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get user by ID"""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.put("/users/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update user (admin only)"""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    update_data = user_update.dict(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    # Update user
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    # Log admin action
    await log_audit_event(
        db=db,
        user_id=current_user.id,
        action="admin_user_updated",
        resource="admin_users",
        details=f"Updated user {user_id}, fields: {', '.join(update_data.keys())}",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    return user

@router.post("/users/{user_id}/activate", response_model=SuccessResponse)
async def activate_user_endpoint(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Activate a user"""
    success = activate_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Log admin action
    await log_audit_event(
        db=db,
        user_id=current_user.id,
        action="admin_user_activated",
        resource="admin_users",
        details=f"Activated user {user_id}",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    return {"success": True, "message": "User activated successfully"}

@router.post("/users/{user_id}/deactivate", response_model=SuccessResponse)
async def deactivate_user_endpoint(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Deactivate a user"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    success = deactivate_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Log admin action
    await log_audit_event(
        db=db,
        user_id=current_user.id,
        action="admin_user_deactivated",
        resource="admin_users",
        details=f"Deactivated user {user_id}",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    return {"success": True, "message": "User deactivated successfully"}

@router.post("/users/{user_id}/promote", response_model=SuccessResponse)
async def promote_user_to_admin(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Promote user to admin"""
    success = promote_to_admin(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Log admin action
    await log_audit_event(
        db=db,
        user_id=current_user.id,
        action="admin_user_promoted",
        resource="admin_users",
        details=f"Promoted user {user_id} to admin",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    return {"success": True, "message": "User promoted to admin successfully"}

@router.post("/users/{user_id}/revoke-admin", response_model=SuccessResponse)
async def revoke_admin_privileges(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Revoke admin privileges"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke your own admin privileges"
        )
    
    success = revoke_admin(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Log admin action
    await log_audit_event(
        db=db,
        user_id=current_user.id,
        action="admin_user_admin_revoked",
        resource="admin_users",
        details=f"Revoked admin privileges from user {user_id}",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    return {"success": True, "message": "Admin privileges revoked successfully"}

@router.delete("/users/{user_id}", response_model=SuccessResponse)
async def delete_user_endpoint(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a user permanently"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    success = delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Log admin action
    await log_audit_event(
        db=db,
        user_id=current_user.id,
        action="admin_user_deleted",
        resource="admin_users",
        details=f"Permanently deleted user {user_id}",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    return {"success": True, "message": "User deleted successfully"}

@router.get("/stats")
async def get_stats(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get system statistics"""
    return get_system_stats(db)