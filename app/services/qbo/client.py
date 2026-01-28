"""
QuickBooks Online API Client

Handles OAuth, API calls, and common operations.
"""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from intuitlib.client import AuthClient
from intuitlib.enums import Scopes
from quickbooks import QuickBooks
from quickbooks.objects.customer import Customer
from quickbooks.objects.vendor import Vendor
from quickbooks.objects.account import Account
from quickbooks.objects.purchase import Purchase
from quickbooks.objects.bill import Bill
from quickbooks.objects.attachable import Attachable, AttachableRef


class QBOClient:
    """
    QuickBooks Online API client.
    
    Handles:
    - OAuth authentication
    - Vendor management
    - Expense/Bill creation
    - Bank feed access
    - Document attachments
    """
    
    def __init__(
        self,
        client_id: str = None,
        client_secret: str = None,
        redirect_uri: str = None,
        environment: str = "sandbox",
    ):
        """
        Initialize QBO client.
        
        Args:
            client_id: Intuit OAuth client ID
            client_secret: Intuit OAuth client secret
            redirect_uri: OAuth callback URL
            environment: "sandbox" or "production"
        """
        self.client_id = client_id or os.getenv("QBO_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("QBO_CLIENT_SECRET")
        self.redirect_uri = redirect_uri or os.getenv("QBO_REDIRECT_URI")
        self.environment = environment or os.getenv("QBO_ENVIRONMENT", "sandbox")
        
        self.auth_client = AuthClient(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            environment=self.environment,
        )
        
        self.qb_client: Optional[QuickBooks] = None
        self.realm_id: Optional[str] = None
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
    
    # --- OAuth ---
    
    def get_auth_url(self, state: str = None) -> str:
        """
        Get OAuth authorization URL.
        
        User should be redirected to this URL to authorize the app.
        """
        scopes = [
            Scopes.ACCOUNTING,  # Full accounting access
        ]
        
        return self.auth_client.get_authorization_url(scopes, state_token=state)
    
    def handle_callback(self, auth_code: str, realm_id: str) -> dict:
        """
        Handle OAuth callback - exchange code for tokens.
        
        Args:
            auth_code: Authorization code from callback
            realm_id: Company ID from callback
            
        Returns:
            Dict with token info
        """
        self.auth_client.get_bearer_token(auth_code, realm_id=realm_id)
        
        self.access_token = self.auth_client.access_token
        self.refresh_token = self.auth_client.refresh_token
        self.realm_id = realm_id
        self.token_expires_at = datetime.now() + timedelta(hours=1)
        
        self._init_qb_client()
        
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "realm_id": self.realm_id,
            "expires_at": self.token_expires_at.isoformat(),
        }
    
    def set_tokens(
        self,
        access_token: str,
        refresh_token: str,
        realm_id: str,
        expires_at: datetime = None,
    ):
        """Set tokens from stored credentials."""
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.realm_id = realm_id
        self.token_expires_at = expires_at or datetime.now() + timedelta(hours=1)
        
        self.auth_client.access_token = access_token
        self.auth_client.refresh_token = refresh_token
        self.auth_client.realm_id = realm_id
        
        self._init_qb_client()
    
    def refresh_tokens(self) -> dict:
        """Refresh access token using refresh token."""
        self.auth_client.refresh(refresh_token=self.refresh_token)
        
        self.access_token = self.auth_client.access_token
        self.refresh_token = self.auth_client.refresh_token
        self.token_expires_at = datetime.now() + timedelta(hours=1)
        
        self._init_qb_client()
        
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.token_expires_at.isoformat(),
        }
    
    def _init_qb_client(self):
        """Initialize QuickBooks client with current tokens."""
        self.qb_client = QuickBooks(
            auth_client=self.auth_client,
            refresh_token=self.refresh_token,
            company_id=self.realm_id,
        )
    
    # --- Company Info ---
    
    def get_company_info(self) -> dict:
        """Get connected company information."""
        from quickbooks.objects.companyinfo import CompanyInfo
        
        info = CompanyInfo.get(self.realm_id, qb=self.qb_client)
        
        return {
            "company_name": info.CompanyName,
            "company_id": self.realm_id,
            "country": info.Country,
            "email": info.Email.Address if info.Email else None,
        }
    
    # --- Vendors ---
    
    def get_vendors(self, active_only: bool = True) -> List[dict]:
        """Get list of vendors."""
        vendors = Vendor.all(qb=self.qb_client)
        
        result = []
        for v in vendors:
            if active_only and not v.Active:
                continue
            result.append({
                "id": v.Id,
                "name": v.DisplayName,
                "email": v.PrimaryEmailAddr.Address if v.PrimaryEmailAddr else None,
                "active": v.Active,
            })
        
        return result
    
    def find_vendor(self, name: str) -> Optional[dict]:
        """Find vendor by name (fuzzy match)."""
        vendors = self.get_vendors()
        
        name_lower = name.lower()
        for v in vendors:
            if name_lower in v["name"].lower() or v["name"].lower() in name_lower:
                return v
        
        return None
    
    def create_vendor(self, name: str, email: str = None) -> dict:
        """Create a new vendor."""
        vendor = Vendor()
        vendor.DisplayName = name
        
        if email:
            from quickbooks.objects.base import EmailAddress
            vendor.PrimaryEmailAddr = EmailAddress()
            vendor.PrimaryEmailAddr.Address = email
        
        vendor.save(qb=self.qb_client)
        
        return {
            "id": vendor.Id,
            "name": vendor.DisplayName,
            "email": email,
        }
    
    def get_or_create_vendor(self, name: str) -> dict:
        """Find existing vendor or create new one."""
        existing = self.find_vendor(name)
        if existing:
            return existing
        
        return self.create_vendor(name)
    
    # --- Accounts ---
    
    def get_accounts(self, account_type: str = None) -> List[dict]:
        """
        Get chart of accounts.
        
        Args:
            account_type: Filter by type (Expense, Bank, etc.)
        """
        accounts = Account.all(qb=self.qb_client)
        
        result = []
        for a in accounts:
            if account_type and a.AccountType != account_type:
                continue
            result.append({
                "id": a.Id,
                "name": a.Name,
                "type": a.AccountType,
                "sub_type": a.AccountSubType,
                "fully_qualified_name": a.FullyQualifiedName,
            })
        
        return result
    
    def get_expense_accounts(self) -> List[dict]:
        """Get expense accounts for categorization."""
        return self.get_accounts(account_type="Expense")
    
    def get_bank_accounts(self) -> List[dict]:
        """Get bank accounts."""
        return self.get_accounts(account_type="Bank")
    
    # --- Expenses & Bills ---
    
    def create_expense(
        self,
        vendor_id: str,
        account_id: str,
        amount: Decimal,
        date: str,
        description: str = None,
        bank_account_id: str = None,
    ) -> dict:
        """
        Create an expense (purchase) in QBO.
        
        Args:
            vendor_id: QBO Vendor ID
            account_id: Expense account ID for categorization
            amount: Transaction amount
            date: Transaction date (YYYY-MM-DD)
            description: Line item description
            bank_account_id: Bank account to pay from
        """
        from quickbooks.objects.detailline import AccountBasedExpenseLine, AccountBasedExpenseLineDetail
        
        purchase = Purchase()
        purchase.PaymentType = "Cash"
        purchase.TxnDate = date
        
        # Vendor reference
        purchase.EntityRef = {"value": vendor_id, "type": "Vendor"}
        
        # Bank account (if specified)
        if bank_account_id:
            purchase.AccountRef = {"value": bank_account_id}
        
        # Line item
        line = AccountBasedExpenseLine()
        line.Amount = float(amount)
        line.Description = description
        line.DetailType = "AccountBasedExpenseLineDetail"
        line.AccountBasedExpenseLineDetail = AccountBasedExpenseLineDetail()
        line.AccountBasedExpenseLineDetail.AccountRef = {"value": account_id}
        
        purchase.Line = [line]
        
        purchase.save(qb=self.qb_client)
        
        return {
            "id": purchase.Id,
            "type": "expense",
            "amount": amount,
            "vendor_id": vendor_id,
            "date": date,
        }
    
    def create_bill(
        self,
        vendor_id: str,
        account_id: str,
        amount: Decimal,
        date: str,
        due_date: str = None,
        description: str = None,
    ) -> dict:
        """
        Create a bill (accounts payable) in QBO.
        """
        from quickbooks.objects.detailline import AccountBasedExpenseLine, AccountBasedExpenseLineDetail
        
        bill = Bill()
        bill.TxnDate = date
        bill.DueDate = due_date or date
        
        # Vendor reference
        bill.VendorRef = {"value": vendor_id}
        
        # Line item
        line = AccountBasedExpenseLine()
        line.Amount = float(amount)
        line.Description = description
        line.DetailType = "AccountBasedExpenseLineDetail"
        line.AccountBasedExpenseLineDetail = AccountBasedExpenseLineDetail()
        line.AccountBasedExpenseLineDetail.AccountRef = {"value": account_id}
        
        bill.Line = [line]
        
        bill.save(qb=self.qb_client)
        
        return {
            "id": bill.Id,
            "type": "bill",
            "amount": amount,
            "vendor_id": vendor_id,
            "date": date,
        }
    
    # --- Attachments ---
    
    def upload_attachment(
        self,
        file_path: str,
        file_name: str,
        content_type: str,
        entity_type: str,
        entity_id: str,
    ) -> dict:
        """
        Upload and attach a document to a QBO entity.
        
        Args:
            file_path: Local path to file
            file_name: Display name for attachment
            content_type: MIME type
            entity_type: "Purchase", "Bill", etc.
            entity_id: ID of entity to attach to
        """
        attachable = Attachable()
        attachable.FileName = file_name
        attachable.ContentType = content_type
        
        # Link to entity
        attachable_ref = AttachableRef()
        attachable_ref.EntityRef = {
            "type": entity_type,
            "value": entity_id,
        }
        attachable.AttachableRef = [attachable_ref]
        
        # Upload file
        with open(file_path, "rb") as f:
            attachable.save(qb=self.qb_client, attachable_file=f)
        
        return {
            "id": attachable.Id,
            "file_name": file_name,
            "entity_type": entity_type,
            "entity_id": entity_id,
        }
    
    def attach_to_bank_transaction(
        self,
        file_path: str,
        file_name: str,
        content_type: str,
        bank_transaction_id: str,
    ) -> dict:
        """
        Attach a document (like a check image) to a bank feed transaction.
        
        This is the key feature for matching bank statements to transactions!
        """
        # Bank transactions in QBO are typically matched to Purchase or Deposit
        # We need to find the linked transaction first
        # For now, attach to the Purchase if it exists
        
        return self.upload_attachment(
            file_path=file_path,
            file_name=file_name,
            content_type=content_type,
            entity_type="Purchase",
            entity_id=bank_transaction_id,
        )
    
    # --- Bank Feed (Advanced) ---
    
    def get_bank_transactions(
        self,
        account_id: str,
        start_date: str = None,
        end_date: str = None,
        status: str = "Pending",
    ) -> List[dict]:
        """
        Get bank feed transactions.
        
        Note: This uses the QBO bank feeds API which requires specific setup.
        For MVP, we may need to match against existing transactions instead.
        """
        # QBO doesn't expose raw bank feed easily via the standard API
        # We'll need to query Purchases/Deposits and match by date/amount
        
        # For now, return purchases for the account
        query = f"SELECT * FROM Purchase WHERE AccountRef = '{account_id}'"
        
        if start_date:
            query += f" AND TxnDate >= '{start_date}'"
        if end_date:
            query += f" AND TxnDate <= '{end_date}'"
        
        purchases = Purchase.query(query, qb=self.qb_client)
        
        result = []
        for p in purchases:
            result.append({
                "id": p.Id,
                "date": p.TxnDate,
                "amount": float(p.TotalAmt),
                "vendor": p.EntityRef.name if p.EntityRef else None,
                "type": "purchase",
            })
        
        return result
