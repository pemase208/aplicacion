from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from db import get_database
from dependencies import get_admin_user
from schemas import User, UserCreate, UserUpdate, Response
from models import User as UserModel, Procedure
from auth import create_user, get_password_hash

router = APIRouter()

@router.get("/", response_model=List[User])
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    admin_user: UserModel = Depends(get_admin_user),
    db: Session = Depends(get_database)
):
    """Get all users (admin only)"""
    query = db.query(UserModel)
    
    if search:
        query = query.filter(
            UserModel.username.contains(search) |
            UserModel.email.contains(search) |
            UserModel.full_name.contains(search)
        )
    
    users = query.offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=User)
async def get_user_by_id(
    user_id: int,
    admin_user: UserModel = Depends(get_admin_user),
    db: Session = Depends(get_database)
):
    """Get user by ID (admin only)"""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.post("/", response_model=Response)
async def create_new_user(
    user_data: UserCreate,
    admin_user: UserModel = Depends(get_admin_user),
    db: Session = Depends(get_database)
):
    """Create a new user (admin only)"""
    # Check if username already exists
    existing_user = db.query(UserModel).filter(UserModel.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Check if email already exists
    existing_email = db.query(UserModel).filter(UserModel.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    try:
        new_user = create_user(
            db=db,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            is_admin=False  # Regular users by default
        )
        
        return Response(
            message="User created successfully",
            data={"user_id": new_user.id, "username": new_user.username}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

@router.put("/{user_id}", response_model=Response)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    admin_user: UserModel = Depends(get_admin_user),
    db: Session = Depends(get_database)
):
    """Update user (admin only)"""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Update fields
        if user_update.email is not None:
            # Check if email is already taken
            existing_user = db.query(UserModel).filter(
                UserModel.email == user_update.email,
                UserModel.id != user_id
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already taken"
                )
            user.email = user_update.email
        
        if user_update.username is not None:
            # Check if username is already taken
            existing_user = db.query(UserModel).filter(
                UserModel.username == user_update.username,
                UserModel.id != user_id
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
            user.username = user_update.username
        
        if user_update.full_name is not None:
            user.full_name = user_update.full_name
        
        if user_update.is_active is not None:
            user.is_active = user_update.is_active
        
        if user_update.is_admin is not None:
            user.is_admin = user_update.is_admin
        
        db.commit()
        db.refresh(user)
        
        return Response(
            message="User updated successfully",
            data={"user_id": user.id}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

@router.delete("/{user_id}", response_model=Response)
async def delete_user(
    user_id: int,
    admin_user: UserModel = Depends(get_admin_user),
    db: Session = Depends(get_database)
):
    """Delete user (admin only)"""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deletion of the current admin user
    if user.id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own admin account"
        )
    
    try:
        db.delete(user)
        db.commit()
        
        return Response(
            message="User deleted successfully",
            data={"deleted_user_id": user_id}
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )

@router.get("/{user_id}/stats")
async def get_user_stats(
    user_id: int,
    admin_user: UserModel = Depends(get_admin_user),
    db: Session = Depends(get_database)
):
    """Get user statistics (admin only)"""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Count user's procedures
    procedure_count = db.query(Procedure).filter(Procedure.created_by_id == user_id).count()
    
    return {
        "user_id": user_id,
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "created_at": user.created_at,
        "procedure_count": procedure_count
    }