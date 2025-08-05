from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from db import get_database
from dependencies import get_admin_user
from schemas import Procedure, ProcedureCreate, ProcedureUpdate, Response
from models import User as UserModel, Procedure as ProcedureModel, FileUpload

router = APIRouter()

@router.get("/", response_model=List[Procedure])
async def get_all_procedures(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    admin_user: UserModel = Depends(get_admin_user),
    db: Session = Depends(get_database)
):
    """Get all procedures (admin only)"""
    query = db.query(ProcedureModel)
    
    if status_filter:
        query = query.filter(ProcedureModel.status == status_filter)
    
    if search:
        query = query.filter(
            ProcedureModel.title.contains(search) |
            ProcedureModel.description.contains(search)
        )
    
    procedures = query.offset(skip).limit(limit).all()
    return procedures

@router.get("/{procedure_id}", response_model=Procedure)
async def get_procedure_by_id(
    procedure_id: int,
    admin_user: UserModel = Depends(get_admin_user),
    db: Session = Depends(get_database)
):
    """Get procedure by ID (admin only)"""
    procedure = db.query(ProcedureModel).filter(ProcedureModel.id == procedure_id).first()
    if not procedure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procedure not found"
        )
    return procedure

@router.post("/", response_model=Response)
async def create_procedure(
    procedure_data: ProcedureCreate,
    admin_user: UserModel = Depends(get_admin_user),
    db: Session = Depends(get_database)
):
    """Create a new procedure (admin only)"""
    try:
        new_procedure = ProcedureModel(
            title=procedure_data.title,
            description=procedure_data.description,
            status=procedure_data.status,
            created_by_id=admin_user.id
        )
        
        db.add(new_procedure)
        db.commit()
        db.refresh(new_procedure)
        
        return Response(
            message="Procedure created successfully",
            data={"procedure_id": new_procedure.id, "title": new_procedure.title}
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create procedure"
        )

@router.put("/{procedure_id}", response_model=Response)
async def update_procedure(
    procedure_id: int,
    procedure_update: ProcedureUpdate,
    admin_user: UserModel = Depends(get_admin_user),
    db: Session = Depends(get_database)
):
    """Update procedure (admin only)"""
    procedure = db.query(ProcedureModel).filter(ProcedureModel.id == procedure_id).first()
    if not procedure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procedure not found"
        )
    
    try:
        # Update fields
        if procedure_update.title is not None:
            procedure.title = procedure_update.title
        
        if procedure_update.description is not None:
            procedure.description = procedure_update.description
        
        if procedure_update.status is not None:
            procedure.status = procedure_update.status
        
        db.commit()
        db.refresh(procedure)
        
        return Response(
            message="Procedure updated successfully",
            data={"procedure_id": procedure.id}
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update procedure"
        )

@router.delete("/{procedure_id}", response_model=Response)
async def delete_procedure(
    procedure_id: int,
    admin_user: UserModel = Depends(get_admin_user),
    db: Session = Depends(get_database)
):
    """Delete procedure (admin only)"""
    procedure = db.query(ProcedureModel).filter(ProcedureModel.id == procedure_id).first()
    if not procedure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procedure not found"
        )
    
    try:
        # Delete associated files first
        files = db.query(FileUpload).filter(FileUpload.procedure_id == procedure_id).all()
        for file in files:
            db.delete(file)
        
        # Delete the procedure
        db.delete(procedure)
        db.commit()
        
        return Response(
            message="Procedure deleted successfully",
            data={"deleted_procedure_id": procedure_id}
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete procedure"
        )

@router.get("/{procedure_id}/files")
async def get_procedure_files(
    procedure_id: int,
    admin_user: UserModel = Depends(get_admin_user),
    db: Session = Depends(get_database)
):
    """Get files associated with a procedure (admin only)"""
    procedure = db.query(ProcedureModel).filter(ProcedureModel.id == procedure_id).first()
    if not procedure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procedure not found"
        )
    
    files = db.query(FileUpload).filter(FileUpload.procedure_id == procedure_id).all()
    
    return {
        "procedure_id": procedure_id,
        "procedure_title": procedure.title,
        "files": [
            {
                "id": file.id,
                "filename": file.filename,
                "original_filename": file.original_filename,
                "file_size": file.file_size,
                "content_type": file.content_type,
                "uploaded_at": file.uploaded_at
            }
            for file in files
        ]
    }

@router.get("/stats/overview")
async def get_procedures_stats(
    admin_user: UserModel = Depends(get_admin_user),
    db: Session = Depends(get_database)
):
    """Get procedures statistics overview (admin only)"""
    total_procedures = db.query(ProcedureModel).count()
    
    # Count by status
    draft_count = db.query(ProcedureModel).filter(ProcedureModel.status == "draft").count()
    active_count = db.query(ProcedureModel).filter(ProcedureModel.status == "active").count()
    completed_count = db.query(ProcedureModel).filter(ProcedureModel.status == "completed").count()
    
    # Recent procedures (last 30 days)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_count = db.query(ProcedureModel).filter(
        ProcedureModel.created_at >= thirty_days_ago
    ).count()
    
    return {
        "total_procedures": total_procedures,
        "by_status": {
            "draft": draft_count,
            "active": active_count,
            "completed": completed_count
        },
        "recent_procedures_30_days": recent_count
    }