from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
import os
import uuid
from typing import Optional
import shutil

from db import get_database
from dependencies import get_admin_user
from schemas import Response, FileUpload as FileUploadSchema
from models import User as UserModel, FileUpload, Procedure

router = APIRouter()

# Upload directory
UPLOAD_DIR = "/app/docs"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@router.post("/file", response_model=Response)
async def upload_file(
    file: UploadFile = File(...),
    procedure_id: Optional[int] = Form(None),
    admin_user: UserModel = Depends(get_admin_user),
    db: Session = Depends(get_database)
):
    """Upload a file (admin only)"""
    
    # Check file size
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE} bytes"
        )
    
    # Validate procedure if provided
    if procedure_id:
        procedure = db.query(Procedure).filter(Procedure.id == procedure_id).first()
        if not procedure:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Procedure not found"
            )
    
    try:
        # Create upload directory if it doesn't exist
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Create database record
        file_upload = FileUpload(
            filename=unique_filename,
            original_filename=file.filename or "unknown",
            file_path=file_path,
            file_size=file_size,
            content_type=file.content_type,
            procedure_id=procedure_id,
            uploaded_by_id=admin_user.id
        )
        
        db.add(file_upload)
        db.commit()
        db.refresh(file_upload)
        
        return Response(
            message="File uploaded successfully",
            data={
                "file_id": file_upload.id,
                "filename": file_upload.filename,
                "original_filename": file_upload.original_filename,
                "file_size": file_upload.file_size
            }
        )
        
    except Exception as e:
        # Clean up file if database operation fails
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )

@router.post("/multiple", response_model=Response)
async def upload_multiple_files(
    files: list[UploadFile] = File(...),
    procedure_id: Optional[int] = Form(None),
    admin_user: UserModel = Depends(get_admin_user),
    db: Session = Depends(get_database)
):
    """Upload multiple files (admin only)"""
    
    if len(files) > 10:  # Limit number of files
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files allowed per upload"
        )
    
    # Validate procedure if provided
    if procedure_id:
        procedure = db.query(Procedure).filter(Procedure.id == procedure_id).first()
        if not procedure:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Procedure not found"
            )
    
    uploaded_files = []
    failed_files = []
    
    try:
        # Create upload directory if it doesn't exist
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        for file in files:
            try:
                # Check file size
                if file.size and file.size > MAX_FILE_SIZE:
                    failed_files.append({
                        "filename": file.filename,
                        "reason": f"File size exceeds {MAX_FILE_SIZE} bytes"
                    })
                    continue
                
                # Generate unique filename
                file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
                unique_filename = f"{uuid.uuid4()}{file_extension}"
                file_path = os.path.join(UPLOAD_DIR, unique_filename)
                
                # Save file to disk
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                # Get file size
                file_size = os.path.getsize(file_path)
                
                # Create database record
                file_upload = FileUpload(
                    filename=unique_filename,
                    original_filename=file.filename or "unknown",
                    file_path=file_path,
                    file_size=file_size,
                    content_type=file.content_type,
                    procedure_id=procedure_id,
                    uploaded_by_id=admin_user.id
                )
                
                db.add(file_upload)
                db.commit()
                db.refresh(file_upload)
                
                uploaded_files.append({
                    "file_id": file_upload.id,
                    "filename": file_upload.filename,
                    "original_filename": file_upload.original_filename,
                    "file_size": file_upload.file_size
                })
                
            except Exception as e:
                failed_files.append({
                    "filename": file.filename,
                    "reason": str(e)
                })
                # Clean up file if it was created
                if 'file_path' in locals() and os.path.exists(file_path):
                    os.remove(file_path)
        
        return Response(
            message=f"Uploaded {len(uploaded_files)} files successfully",
            data={
                "uploaded_files": uploaded_files,
                "failed_files": failed_files,
                "total_uploaded": len(uploaded_files),
                "total_failed": len(failed_files)
            }
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload files"
        )

@router.get("/files")
async def list_uploaded_files(
    admin_user: UserModel = Depends(get_admin_user),
    db: Session = Depends(get_database)
):
    """List all uploaded files (admin only)"""
    files = db.query(FileUpload).order_by(FileUpload.uploaded_at.desc()).all()
    
    return {
        "total_files": len(files),
        "files": [
            {
                "id": file.id,
                "filename": file.filename,
                "original_filename": file.original_filename,
                "file_size": file.file_size,
                "content_type": file.content_type,
                "procedure_id": file.procedure_id,
                "uploaded_by_id": file.uploaded_by_id,
                "uploaded_at": file.uploaded_at
            }
            for file in files
        ]
    }

@router.delete("/file/{file_id}", response_model=Response)
async def delete_uploaded_file(
    file_id: int,
    admin_user: UserModel = Depends(get_admin_user),
    db: Session = Depends(get_database)
):
    """Delete an uploaded file (admin only)"""
    file_upload = db.query(FileUpload).filter(FileUpload.id == file_id).first()
    if not file_upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    try:
        # Delete file from disk
        if os.path.exists(file_upload.file_path):
            os.remove(file_upload.file_path)
        
        # Delete database record
        db.delete(file_upload)
        db.commit()
        
        return Response(
            message="File deleted successfully",
            data={"deleted_file_id": file_id}
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )