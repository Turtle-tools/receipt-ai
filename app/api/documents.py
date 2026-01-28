"""
Document upload and processing endpoints.

This is the main API for document processing:
1. Upload document
2. Classify & extract
3. Match to QBO bank feed
4. Push to QBO with attachments
"""

import os
from typing import Optional, List
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

from app.schemas.documents import (
    DocumentType,
    ProcessingStatus,
    DocumentUploadResponse,
    ExtractionResponse,
    ReceiptData,
    BankStatementData,
    CheckData,
    BankStatementMatchResponse,
    PushToQBOResponse,
    TransactionMatch,
)


router = APIRouter()


# In-memory storage for demo (replace with database)
documents_db = {}


class DocumentStatus(BaseModel):
    """Current status of a document."""
    id: str
    filename: str
    status: ProcessingStatus
    document_type: Optional[DocumentType] = None
    storage_key: Optional[str] = None
    error: Optional[str] = None


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    company_id: str = "default",
    auto_process: bool = True,
    background_tasks: BackgroundTasks = None,
):
    """
    Upload a document for processing.
    
    Supported formats:
    - PDF (bank statements, invoices, multi-page docs)
    - PNG, JPG, JPEG (receipts, checks, single images)
    - HEIC (iPhone photos)
    
    Args:
        file: The document file
        company_id: Company/user identifier for organization
        auto_process: Automatically classify and extract (default: true)
    """
    # Validate file type
    allowed_types = [
        "application/pdf",
        "image/png", 
        "image/jpeg", 
        "image/jpg",
        "image/heic",
    ]
    
    content_type = file.content_type or "application/octet-stream"
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{content_type}' not supported. Use PDF, PNG, JPG, or HEIC."
        )
    
    # Generate document ID
    import uuid
    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    
    # Read file content
    content = await file.read()
    
    # Store document info (in production, save to database)
    documents_db[doc_id] = {
        "id": doc_id,
        "filename": file.filename,
        "content_type": content_type,
        "content": content,  # In production, store in S3/R2
        "company_id": company_id,
        "status": ProcessingStatus.UPLOADED,
        "document_type": None,
        "extracted_data": None,
    }
    
    # Queue processing if auto_process
    if auto_process and background_tasks:
        background_tasks.add_task(process_document, doc_id)
    
    return DocumentUploadResponse(
        id=doc_id,
        filename=file.filename,
        status=ProcessingStatus.UPLOADED,
        message="Document uploaded successfully. Processing started." if auto_process else "Document uploaded. Call /extract to process.",
    )


@router.get("/{document_id}", response_model=DocumentStatus)
async def get_document(document_id: str):
    """Get document status and details."""
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = documents_db[document_id]
    return DocumentStatus(
        id=doc["id"],
        filename=doc["filename"],
        status=doc["status"],
        document_type=doc.get("document_type"),
        storage_key=doc.get("storage_key"),
    )


@router.post("/{document_id}/extract", response_model=ExtractionResponse)
async def extract_document(document_id: str):
    """
    Manually trigger AI extraction for a document.
    
    The AI will:
    1. Classify the document type
    2. Extract relevant data based on type
    3. Store results for review
    """
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = documents_db[document_id]
    
    # Check if already extracted
    if doc["status"] == ProcessingStatus.EXTRACTED:
        return _build_extraction_response(doc)
    
    # Process the document
    await process_document(document_id)
    
    # Return updated data
    doc = documents_db[document_id]
    return _build_extraction_response(doc)


@router.get("/{document_id}/extracted", response_model=ExtractionResponse)
async def get_extracted_data(document_id: str):
    """Get the extracted data for a document."""
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = documents_db[document_id]
    
    if doc["status"] not in [ProcessingStatus.EXTRACTED, ProcessingStatus.MATCHED, ProcessingStatus.PUSHED]:
        raise HTTPException(
            status_code=400, 
            detail=f"Document not yet extracted. Current status: {doc['status']}"
        )
    
    return _build_extraction_response(doc)


@router.post("/{document_id}/match-to-qbo", response_model=BankStatementMatchResponse)
async def match_to_qbo(document_id: str):
    """
    Match extracted transactions to QBO bank feed.
    
    Only works for bank statements. Will:
    1. Get unmatched transactions from QBO bank feed
    2. Match extracted transactions by amount, date, check number
    3. Link check images to matched transactions
    4. Return match results for review
    """
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = documents_db[document_id]
    
    if doc["document_type"] != DocumentType.BANK_STATEMENT:
        raise HTTPException(
            status_code=400,
            detail="Matching only available for bank statements"
        )
    
    if not doc.get("extracted_data"):
        raise HTTPException(
            status_code=400,
            detail="Document not yet extracted"
        )
    
    # TODO: Actually call QBO and matching service
    # For now, return placeholder
    
    return BankStatementMatchResponse(
        id=document_id,
        total_transactions=0,
        matched_transactions=0,
        unmatched_transactions=0,
        vendors_created=0,
        matches=[],
    )


@router.post("/{document_id}/push-to-qbo", response_model=PushToQBOResponse)
async def push_to_qbo(
    document_id: str,
    create_as: str = "expense",  # expense, bill
    auto_create_vendors: bool = True,
    attach_documents: bool = True,
):
    """
    Push extracted data to QuickBooks Online.
    
    Args:
        create_as: Create as "expense" or "bill"
        auto_create_vendors: Create vendors if not found in QBO
        attach_documents: Attach source documents to transactions
    
    For bank statements:
    - Matches transactions to bank feed
    - Creates/matches vendors
    - Attaches check images to check transactions
    - Categorizes based on vendor history
    
    For receipts/invoices:
    - Creates expense or bill
    - Creates vendor if needed
    - Attaches receipt image
    """
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = documents_db[document_id]
    
    if create_as not in ["expense", "bill"]:
        raise HTTPException(
            status_code=400,
            detail="create_as must be 'expense' or 'bill'"
        )
    
    # TODO: Implement actual QBO push
    
    return PushToQBOResponse(
        id=document_id,
        success=False,
        transactions_pushed=0,
        attachments_uploaded=0,
        vendors_created=0,
        errors=["QBO integration not configured"],
    )


# --- Background processing ---

async def process_document(document_id: str):
    """
    Process a document: classify and extract.
    
    This runs in background after upload.
    """
    if document_id not in documents_db:
        return
    
    doc = documents_db[document_id]
    
    try:
        # Update status
        doc["status"] = ProcessingStatus.CLASSIFYING
        
        # Get AI extractor
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            doc["status"] = ProcessingStatus.FAILED
            doc["error"] = "No AI API key configured"
            return
        
        provider = "openai" if os.getenv("OPENAI_API_KEY") else "anthropic"
        
        from app.services.extraction.extractor import DocumentExtractor
        extractor = DocumentExtractor(api_key=api_key, provider=provider)
        
        content = doc["content"]
        
        # Classify document
        doc_type = extractor.classify_document(content)
        doc["document_type"] = doc_type
        doc["status"] = ProcessingStatus.EXTRACTING
        
        # Extract based on type
        if doc_type == DocumentType.RECEIPT or doc_type == DocumentType.INVOICE:
            extracted = extractor.extract_receipt(content)
            doc["extracted_data"] = extracted.model_dump()
            
        elif doc_type == DocumentType.BANK_STATEMENT:
            # For PDF, we'd need to convert to images first
            # For now, treat single image as one page
            extracted = extractor.extract_bank_statement([content])
            doc["extracted_data"] = extracted.model_dump()
            
        elif doc_type == DocumentType.CHECK:
            extracted = extractor.extract_check(content)
            doc["extracted_data"] = extracted.model_dump()
            
        else:
            doc["extracted_data"] = {"raw_type": str(doc_type)}
        
        doc["status"] = ProcessingStatus.EXTRACTED
        
    except Exception as e:
        doc["status"] = ProcessingStatus.FAILED
        doc["error"] = str(e)


def _build_extraction_response(doc: dict) -> ExtractionResponse:
    """Build ExtractionResponse from document dict."""
    response = ExtractionResponse(
        id=doc["id"],
        document_type=doc.get("document_type", DocumentType.UNKNOWN),
        status=doc["status"],
    )
    
    extracted = doc.get("extracted_data")
    if not extracted:
        return response
    
    doc_type = doc.get("document_type")
    
    if doc_type in [DocumentType.RECEIPT, DocumentType.INVOICE]:
        response.receipt_data = ReceiptData(**extracted)
    elif doc_type == DocumentType.BANK_STATEMENT:
        response.bank_statement_data = BankStatementData(**extracted)
    elif doc_type == DocumentType.CHECK:
        response.check_data = CheckData(**extracted)
    
    return response
