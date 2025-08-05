from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import List
import aiofiles
import os
import uuid
from datetime import datetime

from db import get_db
from models import User, Upload
from schemas import UploadResponse, SuccessResponse
from dependencies import get_current_admin_user, get_client_ip, get_user_agent
from audit import log_audit_event

router = APIRouter()

# Upload configuration
UPLOAD_DIR = "/app/uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".txt", ".csv", ".xlsx", ".docx"}

def ensure_upload_directory():
    """Ensure upload directory exists"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_file_extension(filename: str) -> str:
    """Get file extension"""
    return os.path.splitext(filename)[1].lower()

def is_allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return get_file_extension(filename) in ALLOWED_EXTENSIONS

def generate_unique_filename(original_filename: str) -> str:
    """Generate unique filename while preserving extension"""
    ext = get_file_extension(original_filename)
    unique_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{unique_id}{ext}"

@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Upload a file (admin only)"""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file selected"
        )
    
    # Check file extension
    if not is_allowed_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Ensure upload directory exists
    ensure_upload_directory()
    
    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename)
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        # Create upload record
        upload_record = Upload(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=len(file_content),
            content_type=file.content_type,
            uploaded_by=current_user.id
        )
        
        db.add(upload_record)
        db.commit()
        db.refresh(upload_record)
        
        # Log upload
        await log_audit_event(
            db=db,
            user_id=current_user.id,
            action="admin_file_uploaded",
            resource="admin_upload",
            details=f"Uploaded file: {file.filename} ({len(file_content)} bytes)",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        return upload_record
        
    except Exception as e:
        # Clean up file if database operation fails
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error saving file"
        )

@router.get("/uploads", response_model=List[UploadResponse])
async def list_uploads(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List all uploads (admin only)"""
    uploads = db.query(Upload).filter(
        Upload.is_active == True
    ).order_by(Upload.uploaded_at.desc()).offset(skip).limit(limit).all()
    
    return uploads

@router.get("/uploads/{upload_id}", response_model=UploadResponse)
async def get_upload(
    upload_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get upload details (admin only)"""
    upload = db.query(Upload).filter(
        Upload.id == upload_id,
        Upload.is_active == True
    ).first()
    
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )
    
    return upload

@router.delete("/uploads/{upload_id}", response_model=SuccessResponse)
async def delete_upload(
    upload_id: int,
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete an upload (admin only)"""
    upload = db.query(Upload).filter(
        Upload.id == upload_id,
        Upload.is_active == True
    ).first()
    
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )
    
    try:
        # Mark as inactive in database
        upload.is_active = False
        db.commit()
        
        # Delete physical file
        if os.path.exists(upload.file_path):
            os.remove(upload.file_path)
        
        # Log deletion
        await log_audit_event(
            db=db,
            user_id=current_user.id,
            action="admin_file_deleted",
            resource="admin_upload",
            details=f"Deleted file: {upload.original_filename}",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        return {"success": True, "message": "File deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting file"
        )

@router.get("/uploads/stats")
async def get_upload_stats(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get upload statistics (admin only)"""
    from sqlalchemy import func
    
    stats = db.query(
        func.count(Upload.id).label("total_uploads"),
        func.sum(Upload.file_size).label("total_size"),
        func.avg(Upload.file_size).label("average_size")
    ).filter(Upload.is_active == True).first()
    
    # Get uploads by content type
    content_type_stats = db.query(
        Upload.content_type,
        func.count(Upload.id).label("count")
    ).filter(Upload.is_active == True).group_by(Upload.content_type).all()
    
    return {
        "total_uploads": stats.total_uploads or 0,
        "total_size_bytes": stats.total_size or 0,
        "average_size_bytes": float(stats.average_size or 0),
        "content_type_distribution": [
            {"content_type": ct.content_type, "count": ct.count}
            for ct in content_type_stats
        ]
    }