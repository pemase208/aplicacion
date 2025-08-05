from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from db import get_db
from models import User
from schemas import Token, LoginRequest, UserCreate, User as UserSchema, Message
from auth import authenticate_user, create_access_token, create_user, ACCESS_TOKEN_EXPIRE_MINUTES
from audit import log_audit_event
from dependencies import get_client_ip, get_user_agent

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
    login_request: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, login_request.username, login_request.password)
    if not user:
        # Log failed login attempt
        await log_audit_event(
            db=db,
            user_id=None,
            action="login_failed",
            resource="auth",
            details=f"Failed login attempt for username: {login_request.username}",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Log successful login
    await log_audit_event(
        db=db,
        user_id=user.id,
        action="login_success",
        resource="auth",
        details="User logged in successfully",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserSchema)
async def register(
    user_create: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.username == user_create.username) | 
        (User.email == user_create.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create new user
    try:
        new_user = create_user(
            db=db,
            username=user_create.username,
            email=user_create.email,
            password=user_create.password,
            full_name=user_create.full_name
        )
        
        # Log user registration
        await log_audit_event(
            db=db,
            user_id=new_user.id,
            action="user_registered",
            resource="auth",
            details="New user registered",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        return new_user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        )