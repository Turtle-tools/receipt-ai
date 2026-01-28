"""QuickBooks Online OAuth and integration endpoints"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class QBOConnectionStatus(BaseModel):
    """QuickBooks Online connection status"""
    connected: bool
    company_name: Optional[str] = None
    company_id: Optional[str] = None
    expires_at: Optional[str] = None


@router.get("/connect")
async def connect_qbo():
    """
    Initiate QuickBooks Online OAuth flow.
    Redirects user to Intuit authorization page.
    """
    # TODO: Generate OAuth URL and redirect
    # auth_url = qbo_service.get_auth_url()
    # return RedirectResponse(url=auth_url)
    
    return {"status": "not_implemented", "message": "QBO OAuth not configured"}


@router.get("/callback")
async def qbo_callback(code: str, state: str, realmId: str):
    """
    OAuth callback from QuickBooks.
    Exchanges code for access/refresh tokens.
    """
    # TODO: Exchange code for tokens
    # TODO: Store tokens securely
    # TODO: Fetch company info
    
    return {"status": "not_implemented", "code": code, "realmId": realmId}


@router.get("/status", response_model=QBOConnectionStatus)
async def qbo_status():
    """Check if QuickBooks Online is connected"""
    # TODO: Check stored tokens
    return QBOConnectionStatus(
        connected=False,
        company_name=None,
        company_id=None,
    )


@router.post("/disconnect")
async def disconnect_qbo():
    """Disconnect QuickBooks Online integration"""
    # TODO: Revoke tokens, clear stored credentials
    return {"status": "disconnected"}


@router.get("/accounts")
async def get_qbo_accounts():
    """Get chart of accounts from QuickBooks for categorization"""
    # TODO: Fetch accounts from QBO
    return {"accounts": [], "status": "not_implemented"}


@router.get("/vendors")
async def get_qbo_vendors():
    """Get vendor list from QuickBooks for matching"""
    # TODO: Fetch vendors from QBO
    return {"vendors": [], "status": "not_implemented"}
