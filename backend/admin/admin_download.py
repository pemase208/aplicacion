from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import zipfile
import tempfile
from typing import List

from db import get_db
from models import User, Upload, AuditLog
from dependencies import get_current_admin_user, get_client_ip, get_user_agent
from audit import log_audit_event

router = APIRouter()

@router.get("/download/{upload_id}")
async def download_file(
    upload_id: int,
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Download a specific file (admin only)"""
    upload = db.query(Upload).filter(
        Upload.id == upload_id,
        Upload.is_active == True
    ).first()
    
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    if not os.path.exists(upload.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physical file not found"
        )
    
    # Log download
    await log_audit_event(
        db=db,
        user_id=current_user.id,
        action="admin_file_downloaded",
        resource="admin_download",
        details=f"Downloaded file: {upload.original_filename}",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    return FileResponse(
        path=upload.file_path,
        filename=upload.original_filename,
        media_type=upload.content_type
    )

@router.get("/download/bulk")
async def download_multiple_files(
    upload_ids: str,  # Comma-separated list of upload IDs
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Download multiple files as a ZIP archive (admin only)"""
    try:
        # Parse upload IDs
        ids = [int(id.strip()) for id in upload_ids.split(',') if id.strip().isdigit()]
        
        if not ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid upload IDs provided"
            )
        
        # Get uploads
        uploads = db.query(Upload).filter(
            Upload.id.in_(ids),
            Upload.is_active == True
        ).all()
        
        if not uploads:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No files found"
            )
        
        # Create temporary ZIP file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
            with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for upload in uploads:
                    if os.path.exists(upload.file_path):
                        # Add file to ZIP with original filename
                        zipf.write(upload.file_path, upload.original_filename)
            
            # Log bulk download
            await log_audit_event(
                db=db,
                user_id=current_user.id,
                action="admin_bulk_download",
                resource="admin_download",
                details=f"Downloaded {len(uploads)} files as ZIP",
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request)
            )
            
            # Return ZIP file
            return FileResponse(
                path=temp_zip.name,
                filename=f"files_{len(uploads)}_items.zip",
                media_type="application/zip"
            )
            
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid upload IDs format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating download archive"
        )

@router.get("/export/audit-logs")
async def export_audit_logs(
    request: Request,
    format: str = "csv",  # csv or json
    limit: int = 1000,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Export audit logs (admin only)"""
    if format not in ["csv", "json"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format must be 'csv' or 'json'"
        )
    
    # Get audit logs
    audit_logs = db.query(AuditLog).order_by(
        AuditLog.timestamp.desc()
    ).limit(limit).all()
    
    if format == "csv":
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            "ID", "User ID", "Action", "Resource", "Details",
            "IP Address", "User Agent", "Timestamp"
        ])
        
        # Write data
        for log in audit_logs:
            writer.writerow([
                log.id,
                log.user_id,
                log.action,
                log.resource,
                log.details,
                log.ip_address,
                log.user_agent,
                log.timestamp.isoformat() if log.timestamp else ""
            ])
        
        # Log export
        await log_audit_event(
            db=db,
            user_id=current_user.id,
            action="admin_audit_logs_exported",
            resource="admin_download",
            details=f"Exported {len(audit_logs)} audit logs as CSV",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=audit_logs.csv"}
        )
    
    elif format == "json":
        import json
        
        data = []
        for log in audit_logs:
            data.append({
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "resource": log.resource,
                "details": log.details,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None
            })
        
        # Log export
        await log_audit_event(
            db=db,
            user_id=current_user.id,
            action="admin_audit_logs_exported",
            resource="admin_download",
            details=f"Exported {len(audit_logs)} audit logs as JSON",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        return Response(
            content=json.dumps(data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=audit_logs.json"}
        )

@router.get("/export/users")
async def export_users(
    request: Request,
    format: str = "csv",  # csv or json
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Export users list (admin only)"""
    if format not in ["csv", "json"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format must be 'csv' or 'json'"
        )
    
    # Get all users
    users = db.query(User).all()
    
    if format == "csv":
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            "ID", "Username", "Email", "Full Name",
            "Is Active", "Is Admin", "Created At", "Updated At"
        ])
        
        # Write data
        for user in users:
            writer.writerow([
                user.id,
                user.username,
                user.email,
                user.full_name,
                user.is_active,
                user.is_admin,
                user.created_at.isoformat() if user.created_at else "",
                user.updated_at.isoformat() if user.updated_at else ""
            ])
        
        # Log export
        await log_audit_event(
            db=db,
            user_id=current_user.id,
            action="admin_users_exported",
            resource="admin_download",
            details=f"Exported {len(users)} users as CSV",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=users.csv"}
        )
    
    elif format == "json":
        import json
        
        data = []
        for user in users:
            data.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            })
        
        # Log export
        await log_audit_event(
            db=db,
            user_id=current_user.id,
            action="admin_users_exported",
            resource="admin_download",
            details=f"Exported {len(users)} users as JSON",
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        return Response(
            content=json.dumps(data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=users.json"}
        )