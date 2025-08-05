from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

class User(UserBase):
    id: int
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserInDB(User):
    hashed_password: str

# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

# Procedure schemas
class ProcedureBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "draft"

class ProcedureCreate(ProcedureBase):
    pass

class ProcedureUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class Procedure(ProcedureBase):
    id: int
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# File upload schemas
class FileUploadBase(BaseModel):
    filename: str
    original_filename: str
    file_size: Optional[int] = None
    content_type: Optional[str] = None

class FileUpload(FileUploadBase):
    id: int
    file_path: str
    procedure_id: Optional[int] = None
    uploaded_by_id: int
    uploaded_at: datetime
    
    class Config:
        from_attributes = True

# Audit log schemas
class AuditLogBase(BaseModel):
    action: str
    resource: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class AuditLog(AuditLogBase):
    id: int
    user_id: Optional[int] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True

# Response schemas
class Response(BaseModel):
    message: str
    data: Optional[dict] = None

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None