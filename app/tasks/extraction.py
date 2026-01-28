"""
Extraction background tasks.
"""

import logging
from typing import Dict, Any

from app.tasks import celery_app
from app.core.database import get_db_session
from app.services.extraction.extractor import DocumentExtractor
from app.services.storage.storage import StorageService
from app.models.database import Document, ExtractionResult

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="extract_document")
def extract_document(self, document_id: int) -> Dict[str, Any]:
    """
    Extract data from a document.
    
    Args:
        document_id: Document ID to process
        
    Returns:
        Extraction result data
    """
    logger.info(f"Starting extraction for document {document_id}")
    
    with get_db_session() as db:
        # Get document
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ValueError(f"Document {document_id} not found")
        
        # Update status
        doc.status = "processing"
        db.commit()
        
        try:
            # Get file from storage
            storage = StorageService()
            file_data = storage.get_file(doc.storage_path)
            
            # Extract
            extractor = DocumentExtractor()
            result = extractor.extract(
                file_data=file_data,
                file_type=doc.file_type,
                document_type=doc.document_type,
            )
            
            # Save extraction result
            extraction = ExtractionResult(
                document_id=document_id,
                raw_text=result.get("raw_text"),
                structured_data=result.get("structured_data"),
                confidence=result.get("confidence", 0.0),
            )
            db.add(extraction)
            
            # Update document
            doc.status = "extracted"
            doc.extracted_data = result.get("structured_data")
            
            db.commit()
            
            logger.info(f"Extraction complete for document {document_id}")
            
            return {
                "status": "success",
                "document_id": document_id,
                "data": result,
            }
            
        except Exception as e:
            logger.error(f"Extraction failed for document {document_id}: {str(e)}")
            
            doc.status = "failed"
            doc.error_message = str(e)
            db.commit()
            
            raise


@celery_app.task(name="match_bank_transactions")
def match_bank_transactions(document_id: int) -> Dict[str, Any]:
    """
    Match extracted bank transactions with QBO.
    
    Args:
        document_id: Bank statement document ID
        
    Returns:
        Match results
    """
    from app.services.matching.matcher import BankFeedMatcher
    
    logger.info(f"Starting bank transaction matching for document {document_id}")
    
    with get_db_session() as db:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ValueError(f"Document {document_id} not found")
        
        if doc.document_type != "bank_statement":
            raise ValueError("Document is not a bank statement")
        
        try:
            matcher = BankFeedMatcher()
            matches = matcher.match_transactions(
                bank_transactions=doc.extracted_data.get("transactions", [])
            )
            
            # Store matches
            doc.matched_transactions = matches
            db.commit()
            
            logger.info(f"Matched {len(matches)} transactions for document {document_id}")
            
            return {
                "status": "success",
                "document_id": document_id,
                "matches": matches,
            }
            
        except Exception as e:
            logger.error(f"Matching failed: {str(e)}")
            raise


@celery_app.task(name="push_to_qbo")
def push_to_qbo(document_id: int) -> Dict[str, Any]:
    """
    Push extracted data to QuickBooks Online.
    
    Args:
        document_id: Document ID
        
    Returns:
        Push result
    """
    from app.services.qbo.client import QBOClient
    
    logger.info(f"Pushing document {document_id} to QBO")
    
    with get_db_session() as db:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ValueError(f"Document {document_id} not found")
        
        try:
            qbo = QBOClient()
            
            if doc.document_type == "receipt":
                # Create expense/bill
                result = qbo.create_expense(doc.extracted_data)
            elif doc.document_type == "invoice":
                # Create invoice
                result = qbo.create_invoice(doc.extracted_data)
            elif doc.document_type == "check":
                # Create check transaction
                result = qbo.create_check(doc.extracted_data)
            else:
                raise ValueError(f"Unsupported document type: {doc.document_type}")
            
            # Update document
            doc.qbo_id = result.get("id")
            doc.qbo_sync_status = "synced"
            db.commit()
            
            logger.info(f"Successfully pushed document {document_id} to QBO")
            
            return {
                "status": "success",
                "document_id": document_id,
                "qbo_id": result.get("id"),
            }
            
        except Exception as e:
            logger.error(f"QBO push failed: {str(e)}")
            doc.qbo_sync_status = "failed"
            doc.error_message = str(e)
            db.commit()
            raise


@celery_app.task(name="cleanup_old_files")
def cleanup_old_files(days: int = 90) -> Dict[str, Any]:
    """
    Clean up old uploaded files.
    
    Args:
        days: Delete files older than this many days
        
    Returns:
        Cleanup stats
    """
    from datetime import datetime, timedelta
    
    logger.info(f"Cleaning up files older than {days} days")
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    deleted_count = 0
    
    with get_db_session() as db:
        old_docs = db.query(Document).filter(
            Document.created_at < cutoff_date,
            Document.qbo_sync_status == "synced",
        ).all()
        
        storage = StorageService()
        
        for doc in old_docs:
            try:
                storage.delete_file(doc.storage_path)
                doc.storage_path = None
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete file for document {doc.id}: {e}")
        
        db.commit()
    
    logger.info(f"Cleaned up {deleted_count} old files")
    
    return {
        "status": "success",
        "deleted_count": deleted_count,
        "cutoff_date": cutoff_date.isoformat(),
    }
