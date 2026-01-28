"""
AI-powered document extraction service

Uses GPT-4o or Claude for multi-modal document understanding.
"""

import base64
import json
from typing import Optional, List, Tuple
from pathlib import Path

from app.schemas.documents import (
    DocumentType,
    ReceiptData,
    BankStatementData,
    BankTransaction,
    CheckData,
    LineItem,
)


class DocumentExtractor:
    """
    Multi-modal AI extraction for financial documents.
    
    Supports:
    - Receipts & invoices
    - Bank statements (with transaction extraction)
    - Check images (standalone or from statements)
    - Credit card statements
    """
    
    def __init__(self, api_key: str, provider: str = "openai"):
        """
        Initialize extractor with AI provider.
        
        Args:
            api_key: API key for OpenAI or Anthropic
            provider: "openai" or "anthropic"
        """
        self.api_key = api_key
        self.provider = provider
        
        if provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            self.model = "gpt-4o"
        elif provider == "anthropic":
            from anthropic import Anthropic
            self.client = Anthropic(api_key=api_key)
            self.model = "claude-3-5-sonnet-20241022"
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def classify_document(self, image_data: bytes) -> DocumentType:
        """
        Classify document type using vision model.
        
        Returns: DocumentType enum
        """
        prompt = """Classify this financial document into one of these types:
        - receipt: A purchase receipt from a store/restaurant
        - invoice: A bill or invoice from a vendor
        - bank_statement: A bank account statement showing transactions
        - check: An image of a check
        - credit_card_statement: A credit card statement
        - unknown: Cannot determine
        
        Respond with ONLY the type name, nothing else."""
        
        response = self._vision_request(image_data, prompt)
        
        type_map = {
            "receipt": DocumentType.RECEIPT,
            "invoice": DocumentType.INVOICE,
            "bill": DocumentType.BILL,
            "bank_statement": DocumentType.BANK_STATEMENT,
            "check": DocumentType.CHECK,
            "credit_card_statement": DocumentType.CREDIT_CARD_STATEMENT,
        }
        
        return type_map.get(response.strip().lower(), DocumentType.UNKNOWN)
    
    def extract_receipt(self, image_data: bytes) -> ReceiptData:
        """Extract data from receipt or invoice image."""
        
        prompt = """Extract all information from this receipt/invoice.
        
        Return a JSON object with these fields:
        {
            "vendor": "Store/vendor name",
            "vendor_address": "Full address if visible",
            "date": "YYYY-MM-DD format",
            "total_amount": 123.45,
            "subtotal": 100.00,
            "tax_amount": 23.45,
            "tip_amount": null,
            "payment_method": "cash/credit/debit/etc",
            "line_items": [
                {"description": "Item name", "quantity": 1, "unit_price": 10.00, "amount": 10.00}
            ],
            "category_suggestion": "meals/office_supplies/travel/etc"
        }
        
        Use null for any field you cannot determine.
        Return ONLY valid JSON, no explanation."""
        
        response = self._vision_request(image_data, prompt)
        data = self._parse_json(response)
        
        return ReceiptData(
            vendor=data.get("vendor"),
            vendor_address=data.get("vendor_address"),
            date=data.get("date"),
            total_amount=data.get("total_amount"),
            subtotal=data.get("subtotal"),
            tax_amount=data.get("tax_amount"),
            tip_amount=data.get("tip_amount"),
            payment_method=data.get("payment_method"),
            line_items=[LineItem(**item) for item in data.get("line_items", [])],
            category_suggestion=data.get("category_suggestion"),
            confidence=0.85,  # TODO: Calculate based on extraction quality
        )
    
    def extract_bank_statement(self, pdf_pages: List[bytes]) -> BankStatementData:
        """
        Extract all transactions from a bank statement.
        
        Args:
            pdf_pages: List of page images (as bytes)
            
        Returns:
            BankStatementData with all transactions
        """
        # First, extract header info from first page
        header_prompt = """Extract the bank statement header information.
        
        Return JSON:
        {
            "bank_name": "Bank name",
            "account_number_last4": "1234",
            "account_type": "checking/savings",
            "statement_period_start": "YYYY-MM-DD",
            "statement_period_end": "YYYY-MM-DD",
            "beginning_balance": 1000.00,
            "ending_balance": 1500.00
        }
        
        Return ONLY valid JSON."""
        
        header_response = self._vision_request(pdf_pages[0], header_prompt)
        header_data = self._parse_json(header_response)
        
        # Extract transactions from all pages
        all_transactions = []
        for page in pdf_pages:
            txns = self._extract_transactions_from_page(page)
            all_transactions.extend(txns)
        
        # Calculate totals
        total_deposits = sum(t.amount for t in all_transactions if t.amount > 0)
        total_withdrawals = sum(abs(t.amount) for t in all_transactions if t.amount < 0)
        
        return BankStatementData(
            bank_name=header_data.get("bank_name"),
            account_number_last4=header_data.get("account_number_last4"),
            account_type=header_data.get("account_type"),
            statement_period_start=header_data.get("statement_period_start"),
            statement_period_end=header_data.get("statement_period_end"),
            beginning_balance=header_data.get("beginning_balance"),
            ending_balance=header_data.get("ending_balance"),
            total_deposits=total_deposits,
            total_withdrawals=total_withdrawals,
            transactions=all_transactions,
            check_images=[],  # Populated by snip_checks_from_statement
            confidence=0.80,
        )
    
    def _extract_transactions_from_page(self, page_image: bytes) -> List[BankTransaction]:
        """Extract transactions from a single page of bank statement."""
        
        prompt = """Extract ALL transactions from this bank statement page.
        
        For each transaction, return:
        {
            "date": "YYYY-MM-DD",
            "description": "Full description text",
            "amount": -123.45,  // Negative for debits/withdrawals, positive for credits/deposits
            "transaction_type": "check/debit/credit/deposit/transfer/fee/atm",
            "check_number": "1234",  // Only if this is a check, otherwise null
            "running_balance": 1500.00,  // If shown, otherwise null
            "vendor_suggestion": "Likely vendor name"  // Your best guess at the vendor
        }
        
        Return a JSON array of all transactions on this page.
        Return ONLY valid JSON array, no explanation.
        If no transactions on this page, return []."""
        
        response = self._vision_request(page_image, prompt)
        transactions_data = self._parse_json(response)
        
        if not isinstance(transactions_data, list):
            return []
        
        transactions = []
        for txn in transactions_data:
            transactions.append(BankTransaction(
                date=txn.get("date"),
                description=txn.get("description", ""),
                amount=txn.get("amount", 0),
                transaction_type=txn.get("transaction_type", "unknown"),
                check_number=txn.get("check_number"),
                running_balance=txn.get("running_balance"),
                vendor_suggestion=txn.get("vendor_suggestion"),
            ))
        
        return transactions
    
    def extract_check(self, image_data: bytes) -> CheckData:
        """Extract data from a check image."""
        
        prompt = """Extract all information from this check image.
        
        Return JSON:
        {
            "check_number": "1234",
            "payee": "Who the check is made out to",
            "amount": 500.00,
            "date": "YYYY-MM-DD",
            "memo": "Memo line text",
            "bank_name": "Bank name if visible",
            "routing_number": "123456789",  // If visible, otherwise null
            "account_number_last4": "5678"  // Last 4 digits if visible
        }
        
        Return ONLY valid JSON."""
        
        response = self._vision_request(image_data, prompt)
        data = self._parse_json(response)
        
        return CheckData(
            check_number=data.get("check_number"),
            payee=data.get("payee"),
            amount=data.get("amount"),
            date=data.get("date"),
            memo=data.get("memo"),
            bank_name=data.get("bank_name"),
            routing_number=data.get("routing_number"),
            account_number_last4=data.get("account_number_last4"),
            confidence=0.85,
        )
    
    def find_check_regions(self, page_image: bytes) -> List[dict]:
        """
        Find check image regions in a bank statement page.
        
        Returns list of bounding boxes where checks are located.
        """
        prompt = """Look at this bank statement page. 
        Find any check images that appear on the page.
        
        For each check image found, return its approximate location:
        {
            "checks": [
                {
                    "x_percent": 10,  // Left edge as percentage of page width
                    "y_percent": 20,  // Top edge as percentage of page height
                    "width_percent": 40,  // Width as percentage of page width
                    "height_percent": 20,  // Height as percentage of page height
                    "check_number": "1234"  // If visible
                }
            ]
        }
        
        Return empty array if no check images found.
        Return ONLY valid JSON."""
        
        response = self._vision_request(page_image, prompt)
        data = self._parse_json(response)
        
        return data.get("checks", [])
    
    def snip_checks_from_statement(
        self, 
        pdf_pages: List[bytes],
        page_dimensions: List[Tuple[int, int]]
    ) -> List[CheckData]:
        """
        Find and extract check images from bank statement pages.
        
        Args:
            pdf_pages: List of page images
            page_dimensions: List of (width, height) for each page
            
        Returns:
            List of CheckData with extracted check info and image paths
        """
        from PIL import Image
        import io
        
        extracted_checks = []
        
        for i, (page_image, dimensions) in enumerate(zip(pdf_pages, page_dimensions)):
            # Find check regions on this page
            check_regions = self.find_check_regions(page_image)
            
            for region in check_regions:
                # Convert percentage to pixels
                width, height = dimensions
                x = int(region["x_percent"] / 100 * width)
                y = int(region["y_percent"] / 100 * height)
                w = int(region["width_percent"] / 100 * width)
                h = int(region["height_percent"] / 100 * height)
                
                # Crop the check image
                img = Image.open(io.BytesIO(page_image))
                check_img = img.crop((x, y, x + w, y + h))
                
                # Convert back to bytes
                buffer = io.BytesIO()
                check_img.save(buffer, format="PNG")
                check_bytes = buffer.getvalue()
                
                # Extract check data from the cropped image
                check_data = self.extract_check(check_bytes)
                check_data.image_path = None  # Will be set after upload to storage
                
                extracted_checks.append(check_data)
        
        return extracted_checks
    
    def _vision_request(self, image_data: bytes, prompt: str) -> str:
        """Make a vision API request."""
        
        image_b64 = base64.b64encode(image_data).decode("utf-8")
        
        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_b64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4096,
            )
            return response.choices[0].message.content
            
        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_b64,
                                }
                            },
                            {"type": "text", "text": prompt}
                        ]
                    }
                ]
            )
            return response.content[0].text
    
    def _parse_json(self, response: str) -> dict:
        """Parse JSON from AI response, handling markdown code blocks."""
        
        # Remove markdown code blocks if present
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            return {}
