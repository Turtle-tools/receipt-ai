"""Document upload and processing endpoints"""

from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import Optional
from pydantic import BaseModel


router = APIRouter()


class ExtractedData(BaseModel):
    """Data extracted from a document"""
    vendor: Optional[str] = None
    amount: Optional[float] = None
    date: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    line_items: Optional[list] = None
    confidence: float = 0.0
    raw_text: Optional[str] = None


class DocumentResponse(BaseModel):
    """Response for document upload"""
    id: str
    filename: str
    status: str
    extracted: Optional[ExtractedData] = None


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    auto_extract: bool = True,
):
    """
    Upload a document (receipt, invoice, bank statement) for processing.
    
    - **file**: PDF, PNG, JPG, or HEIC file
    - **auto_extract**: Automatically extract data using AI (default: true)
    """
    # Validate file type
    allowed_types = ["application/pdf", "image/png", "image/jpeg", "image/heic"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file.content_type} not supported. Use PDF, PNG, JPG, or HEIC."
        )
    
    # TODO: Save file to storage
    # TODO: If auto_extract, run AI extraction
    
    return DocumentResponse(
        id="doc_placeholder",
        filename=file.filename,
        status="uploaded",
        extracted=None,
    )


@router.get("/{document_id}")
async def get_document(document_id: str):
    """Get document details and extracted data"""
    # TODO: Fetch from database
    return {"id": document_id, "status": "not_implemented"}


@router.post("/{document_id}/extract")
async def extract_document(document_id: str):
    """Manually trigger AI extraction for a document"""
    # TODO: Run extraction service
    return {"id": document_id, "status": "extraction_queued"}


@router.post("/{document_id}/push-to-qbo")
async def push_to_qbo(document_id: str, as_type: str = "expense"):
    """
    Push extracted document data to QuickBooks Online.
    
    - **as_type**: "expense" or "bill"
    """
    if as_type not in ["expense", "bill"]:
        raise HTTPException(status_code=400, detail="as_type must be 'expense' or 'bill'")
    
    # TODO: Call QBO service
    return {"id": document_id, "qbo_status": "not_implemented", "type": as_type}
