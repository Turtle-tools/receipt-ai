"""
Batch processing endpoints for bulk operations.
"""

from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
import zipfile
import io

from app.core.database import get_db
from app.core.auth import get_api_key
from app.models.database import Document
from app.services.storage.storage import StorageService
from app.tasks.extraction import extract_document

router = APIRouter()


class BatchUploadResponse(BaseModel):
    """Response for batch upload."""
    batch_id: str
    total_files: int
    uploaded_documents: List[int]
    failed_files: List[dict]


class BatchJob(BaseModel):
    """Batch processing job status."""
    batch_id: str
    total_files: int
    completed: int
    failed: int
    in_progress: int
    status: str  # pending, processing, completed, failed


@router.post("/upload", response_model=BatchUploadResponse)
async def batch_upload(
    files: List[UploadFile] = File(...),
    company_id: str = "default",
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    """
    Upload multiple files at once.
    
    Accepts up to 100 files per batch.
    Each file is processed independently.
    """
    if len(files) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 files per batch",
        )
    
    import uuid
    batch_id = str(uuid.uuid4())
    
    storage = StorageService()
    uploaded_documents = []
    failed_files = []
    
    for file in files:
        try:
            # Read file
            file_data = await file.read()
            
            # Store
            storage_path = storage.store_file(
                file_data=file_data,
                filename=file.filename,
            )
            
            # Create document
            doc = Document(
                filename=file.filename,
                file_type=file.content_type or "application/octet-stream",
                storage_path=storage_path,
                status="uploaded",
                company_id=company_id,
                source="batch_upload",
                metadata={"batch_id": batch_id},
            )
            
            db.add(doc)
            db.commit()
            db.refresh(doc)
            
            # Queue extraction
            extract_document.delay(doc.id)
            
            uploaded_documents.append(doc.id)
            
        except Exception as e:
            failed_files.append({
                "filename": file.filename,
                "error": str(e),
            })
    
    return BatchUploadResponse(
        batch_id=batch_id,
        total_files=len(files),
        uploaded_documents=uploaded_documents,
        failed_files=failed_files,
    )


@router.post("/upload-zip")
async def batch_upload_zip(
    file: UploadFile = File(...),
    company_id: str = "default",
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    """
    Upload a ZIP file containing multiple documents.
    
    Extracts all files from the ZIP and processes them.
    Supports nested directories.
    """
    if not file.filename.endswith('.zip'):
        raise HTTPException(
            status_code=400,
            detail="File must be a ZIP archive",
        )
    
    # Read ZIP
    zip_data = await file.read()
    zip_file = zipfile.ZipFile(io.BytesIO(zip_data))
    
    import uuid
    batch_id = str(uuid.uuid4())
    
    storage = StorageService()
    uploaded_documents = []
    failed_files = []
    
    # Extract and process each file
    for file_info in zip_file.filelist:
        # Skip directories
        if file_info.is_dir():
            continue
        
        # Skip hidden files
        if file_info.filename.startswith('.') or '/__MACOSX/' in file_info.filename:
            continue
        
        try:
            # Extract file
            file_data = zip_file.read(file_info.filename)
            
            # Get clean filename
            filename = file_info.filename.split('/')[-1]
            
            # Store
            storage_path = storage.store_file(
                file_data=file_data,
                filename=filename,
            )
            
            # Create document
            doc = Document(
                filename=filename,
                file_type="application/octet-stream",  # Will be detected during extraction
                storage_path=storage_path,
                status="uploaded",
                company_id=company_id,
                source="batch_zip",
                metadata={
                    "batch_id": batch_id,
                    "original_path": file_info.filename,
                },
            )
            
            db.add(doc)
            db.commit()
            db.refresh(doc)
            
            # Queue extraction
            extract_document.delay(doc.id)
            
            uploaded_documents.append(doc.id)
            
        except Exception as e:
            failed_files.append({
                "filename": file_info.filename,
                "error": str(e),
            })
    
    return {
        "status": "success",
        "batch_id": batch_id,
        "total_files": len(uploaded_documents) + len(failed_files),
        "uploaded": len(uploaded_documents),
        "failed": len(failed_files),
        "document_ids": uploaded_documents,
        "errors": failed_files,
    }


@router.get("/status/{batch_id}")
async def get_batch_status(
    batch_id: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    """Get status of a batch processing job."""
    
    # Query documents in this batch
    documents = db.query(Document).filter(
        Document.metadata["batch_id"].astext == batch_id
    ).all()
    
    if not documents:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Count statuses
    total = len(documents)
    completed = sum(1 for d in documents if d.status == "extracted")
    failed = sum(1 for d in documents if d.status == "failed")
    in_progress = sum(1 for d in documents if d.status in ["uploaded", "processing"])
    
    # Determine overall status
    if failed == total:
        overall_status = "failed"
    elif completed == total:
        overall_status = "completed"
    elif in_progress > 0:
        overall_status = "processing"
    else:
        overall_status = "pending"
    
    return {
        "status": "success",
        "batch_id": batch_id,
        "total_files": total,
        "completed": completed,
        "failed": failed,
        "in_progress": in_progress,
        "overall_status": overall_status,
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "status": d.status,
                "error": d.error_message,
            }
            for d in documents
        ],
    }


@router.post("/push-all/{batch_id}")
async def push_batch_to_qbo(
    batch_id: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    """
    Push all successfully extracted documents in a batch to QBO.
    
    Only pushes documents with status='extracted' and qbo_sync_status is null.
    """
    from app.tasks.extraction import push_to_qbo
    
    # Get extracted documents in batch
    documents = db.query(Document).filter(
        Document.metadata["batch_id"].astext == batch_id,
        Document.status == "extracted",
        Document.qbo_sync_status == None,
    ).all()
    
    if not documents:
        return {
            "status": "success",
            "message": "No documents ready to push",
            "pushed": 0,
        }
    
    # Queue push tasks
    task_ids = []
    for doc in documents:
        task = push_to_qbo.delay(doc.id)
        task_ids.append(task.id)
    
    return {
        "status": "success",
        "batch_id": batch_id,
        "pushed": len(documents),
        "document_ids": [d.id for d in documents],
        "task_ids": task_ids,
    }
