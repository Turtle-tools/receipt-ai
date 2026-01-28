"""Document schemas for Receipt AI"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from decimal import Decimal
from enum import Enum


class DocumentType(str, Enum):
    """Types of documents we can process"""
    RECEIPT = "receipt"
    INVOICE = "invoice"
    BILL = "bill"
    BANK_STATEMENT = "bank_statement"
    CHECK = "check"
    CREDIT_CARD_STATEMENT = "credit_card_statement"
    UNKNOWN = "unknown"


class ProcessingStatus(str, Enum):
    """Document processing status"""
    UPLOADED = "uploaded"
    CLASSIFYING = "classifying"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    MATCHING = "matching"
    MATCHED = "matched"
    PUSHED = "pushed"
    FAILED = "failed"


# --- Line Items ---

class LineItem(BaseModel):
    """Individual line item from receipt/invoice"""
    description: str
    quantity: Optional[float] = 1.0
    unit_price: Optional[Decimal] = None
    amount: Decimal
    category: Optional[str] = None


# --- Receipt/Invoice Data ---

class ReceiptData(BaseModel):
    """Extracted data from receipt or invoice"""
    vendor: Optional[str] = None
    vendor_address: Optional[str] = None
    date: Optional[date] = None
    total_amount: Optional[Decimal] = None
    subtotal: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    tip_amount: Optional[Decimal] = None
    payment_method: Optional[str] = None
    line_items: List[LineItem] = []
    category_suggestion: Optional[str] = None
    confidence: float = 0.0
    raw_text: Optional[str] = None


# --- Check Data ---

class CheckData(BaseModel):
    """Extracted data from a check image"""
    check_number: Optional[str] = None
    payee: Optional[str] = None
    amount: Optional[Decimal] = None
    date: Optional[date] = None
    memo: Optional[str] = None
    bank_name: Optional[str] = None
    routing_number: Optional[str] = None
    account_number_last4: Optional[str] = None
    confidence: float = 0.0
    image_path: Optional[str] = None  # S3/R2 path to snipped check image


# --- Bank Statement Data ---

class BankTransaction(BaseModel):
    """Single transaction from bank statement"""
    date: date
    description: str
    amount: Decimal  # Negative for debits, positive for credits
    transaction_type: str  # debit, credit, check, deposit, transfer, fee
    check_number: Optional[str] = None
    running_balance: Optional[Decimal] = None
    vendor_suggestion: Optional[str] = None
    category_suggestion: Optional[str] = None
    # Link to extracted check image if this is a check transaction
    check_image: Optional[CheckData] = None


class BankStatementData(BaseModel):
    """Extracted data from bank statement"""
    bank_name: Optional[str] = None
    account_number_last4: Optional[str] = None
    account_type: Optional[str] = None  # checking, savings
    statement_period_start: Optional[date] = None
    statement_period_end: Optional[date] = None
    beginning_balance: Optional[Decimal] = None
    ending_balance: Optional[Decimal] = None
    total_deposits: Optional[Decimal] = None
    total_withdrawals: Optional[Decimal] = None
    transactions: List[BankTransaction] = []
    check_images: List[CheckData] = []  # Extracted check images
    confidence: float = 0.0
    raw_text: Optional[str] = None


# --- QBO Matching ---

class QBOMatchResult(BaseModel):
    """Result of matching to QBO bank feed"""
    matched: bool
    qbo_transaction_id: Optional[str] = None
    match_score: float = 0.0
    match_reasons: List[str] = []


class TransactionMatch(BaseModel):
    """A bank transaction with its QBO match"""
    extracted: BankTransaction
    qbo_match: Optional[QBOMatchResult] = None
    vendor_id: Optional[str] = None  # QBO vendor ID (existing or created)
    category_id: Optional[str] = None  # QBO account ID for categorization
    attachment_uploaded: bool = False


# --- API Responses ---

class DocumentUploadResponse(BaseModel):
    """Response after uploading a document"""
    id: str
    filename: str
    status: ProcessingStatus
    document_type: Optional[DocumentType] = None
    message: str = ""


class ExtractionResponse(BaseModel):
    """Response with extracted data"""
    id: str
    document_type: DocumentType
    status: ProcessingStatus
    receipt_data: Optional[ReceiptData] = None
    bank_statement_data: Optional[BankStatementData] = None
    check_data: Optional[CheckData] = None


class BankStatementMatchResponse(BaseModel):
    """Response after matching bank statement to QBO"""
    id: str
    total_transactions: int
    matched_transactions: int
    unmatched_transactions: int
    vendors_created: int
    matches: List[TransactionMatch] = []


class PushToQBOResponse(BaseModel):
    """Response after pushing to QBO"""
    id: str
    success: bool
    transactions_pushed: int
    attachments_uploaded: int
    vendors_created: int
    errors: List[str] = []
