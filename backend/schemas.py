from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

# Audit log schemas
class AuditLogBase(BaseModel):
    action: str
    resource: Optional[str] = None
    details: Optional[str] = None

class AuditLogCreate(AuditLogBase):
    user_id: int
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class AuditLog(AuditLogBase):
    id: int
    user_id: int
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

# Upload schemas
class UploadResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    uploaded_at: datetime

    class Config:
        from_attributes = True

# Generic response schemas
class Message(BaseModel):
    message: str

class SuccessResponse(BaseModel):
    success: bool
    message: str