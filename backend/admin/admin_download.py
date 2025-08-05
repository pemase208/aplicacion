from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from db import get_database
from dependencies import get_admin_user
from models import User as UserModel, FileUpload

router = APIRouter()

@router.get("/file/{file_id}")
async def download_file(
    file_id: int,
    admin_user: UserModel = Depends(get_admin_user),
    db: Session = Depends(get_database)
):
    """Download a file by ID (admin only)"""
    file_upload = db.query(FileUpload).filter(FileUpload.id == file_id).first()
    if not file_upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Check if file exists on disk
    if not os.path.exists(file_upload.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )
    
    return FileResponse(
        path=file_upload.file_path,
        filename=file_upload.original_filename,
        media_type=file_upload.content_type or 'application/octet-stream'
    )

@router.get("/files/procedure/{procedure_id}")
async def download_procedure_files(
    procedure_id: int,
    admin_user: UserModel = Depends(get_admin_user),
    db: Session = Depends(get_database)
):
    """Get download links for all files in a procedure (admin only)"""
    from models import Procedure
    
    # Check if procedure exists
    procedure = db.query(Procedure).filter(Procedure.id == procedure_id).first()
    if not procedure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procedure not found"
        )
    
    # Get all files for this procedure
    files = db.query(FileUpload).filter(FileUpload.procedure_id == procedure_id).all()
    
    if not files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No files found for this procedure"
        )
    
    # Return file information with download URLs
    return {
        "procedure_id": procedure_id,
        "procedure_title": procedure.title,
        "total_files": len(files),
        "files": [
            {
                "id": file.id,
                "filename": file.filename,
                "original_filename": file.original_filename,
                "file_size": file.file_size,
                "content_type": file.content_type,
                "uploaded_at": file.uploaded_at,
                "download_url": f"/admin/download/file/{file.id}"
            }
            for file in files
            if os.path.exists(file.file_path)  # Only include files that exist on disk
        ]
    }

@router.get("/files/user/{user_id}")
async def download_user_files(
    user_id: int,
    admin_user: UserModel = Depends(get_admin_user),
    db: Session = Depends(get_database)
):
    """Get download links for all files uploaded by a user (admin only)"""
    # Check if user exists
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get all files uploaded by this user
    files = db.query(FileUpload).filter(FileUpload.uploaded_by_id == user_id).all()
    
    if not files:
        return {
            "user_id": user_id,
            "username": user.username,
            "total_files": 0,
            "files": []
        }
    
    # Return file information with download URLs
    return {
        "user_id": user_id,
        "username": user.username,
        "total_files": len(files),
        "files": [
            {
                "id": file.id,
                "filename": file.filename,
                "original_filename": file.original_filename,
                "file_size": file.file_size,
                "content_type": file.content_type,
                "procedure_id": file.procedure_id,
                "uploaded_at": file.uploaded_at,
                "download_url": f"/admin/download/file/{file.id}"
            }
            for file in files
            if os.path.exists(file.file_path)  # Only include files that exist on disk
        ]
    }

@router.get("/files/all")
async def get_all_download_links(
    admin_user: UserModel = Depends(get_admin_user),
    db: Session = Depends(get_database)
):
    """Get download links for all files in the system (admin only)"""
    files = db.query(FileUpload).order_by(FileUpload.uploaded_at.desc()).all()
    
    # Calculate total size and count
    total_files = len(files)
    total_size = sum(file.file_size or 0 for file in files if os.path.exists(file.file_path))
    
    return {
        "total_files": total_files,
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "files": [
            {
                "id": file.id,
                "filename": file.filename,
                "original_filename": file.original_filename,
                "file_size": file.file_size,
                "content_type": file.content_type,
                "procedure_id": file.procedure_id,
                "uploaded_by_id": file.uploaded_by_id,
                "uploaded_at": file.uploaded_at,
                "download_url": f"/admin/download/file/{file.id}",
                "exists_on_disk": os.path.exists(file.file_path)
            }
            for file in files
        ]
    }

@router.get("/stats")
async def get_download_stats(
    admin_user: UserModel = Depends(get_admin_user),
    db: Session = Depends(get_database)
):
    """Get file download statistics (admin only)"""
    total_files = db.query(FileUpload).count()
    
    # Count files by type
    files_by_type = {}
    files = db.query(FileUpload).all()
    
    for file in files:
        content_type = file.content_type or "unknown"
        if content_type not in files_by_type:
            files_by_type[content_type] = 0
        files_by_type[content_type] += 1
    
    # Calculate total storage used
    total_storage = sum(file.file_size or 0 for file in files if os.path.exists(file.file_path))
    
    # Count files that exist vs missing
    existing_files = sum(1 for file in files if os.path.exists(file.file_path))
    missing_files = total_files - existing_files
    
    return {
        "total_files": total_files,
        "existing_files": existing_files,
        "missing_files": missing_files,
        "total_storage_bytes": total_storage,
        "total_storage_mb": round(total_storage / (1024 * 1024), 2),
        "files_by_type": files_by_type
    }