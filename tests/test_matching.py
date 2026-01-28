"""
Tests for bank feed matching service.
"""

import pytest
from datetime import date
from decimal import Decimal

from app.services.matching.matcher import (
    BankFeedMatcher,
    VendorMatcher,
    QBOBankTransaction,
)
from app.schemas.documents import BankTransaction, BankStatementData, CheckData


class TestBankFeedMatcher:
    """Test the bank feed matching logic."""
    
    @pytest.fixture
    def matcher(self):
        return BankFeedMatcher()
    
    @pytest.fixture
    def sample_qbo_transactions(self):
        return [
            QBOBankTransaction(
                id="qbo_1",
                date=date(2026, 1, 15),
                amount=Decimal("-150.00"),
                description="AMAZON PRIME",
                check_number=None,
            ),
            QBOBankTransaction(
                id="qbo_2",
                date=date(2026, 1, 16),
                amount=Decimal("-500.00"),
                description="CHECK 1234",
                check_number="1234",
            ),
            QBOBankTransaction(
                id="qbo_3",
                date=date(2026, 1, 17),
                amount=Decimal("2500.00"),
                description="PAYROLL DEPOSIT",
            ),
        ]
    
    def test_exact_amount_and_date_match(self, matcher, sample_qbo_transactions):
        """Test matching with exact amount and date."""
        extracted = BankTransaction(
            date=date(2026, 1, 15),
            description="Amazon Prime Membership",
            amount=Decimal("-150.00"),
            transaction_type="debit",
        )
        
        statement = BankStatementData(
            transactions=[extracted],
            check_images=[],
        )
        
        matches = matcher.match_statement_to_bank_feed(
            statement, sample_qbo_transactions
        )
        
        assert len(matches) == 1
        assert matches[0].qbo_match.matched == True
        assert matches[0].qbo_match.qbo_transaction_id == "qbo_1"
        assert matches[0].qbo_match.match_score >= 70
    
    def test_check_number_match(self, matcher, sample_qbo_transactions):
        """Test that check numbers boost match confidence."""
        extracted = BankTransaction(
            date=date(2026, 1, 16),
            description="Check payment",
            amount=Decimal("-500.00"),
            transaction_type="check",
            check_number="1234",
        )
        
        statement = BankStatementData(
            transactions=[extracted],
            check_images=[],
        )
        
        matches = matcher.match_statement_to_bank_feed(
            statement, sample_qbo_transactions
        )
        
        assert len(matches) == 1
        assert matches[0].qbo_match.matched == True
        assert matches[0].qbo_match.qbo_transaction_id == "qbo_2"
        # Check number match should give high score
        assert matches[0].qbo_match.match_score >= 80
    
    def test_no_match_wrong_amount(self, matcher, sample_qbo_transactions):
        """Test that wrong amount results in no match."""
        extracted = BankTransaction(
            date=date(2026, 1, 15),
            description="Amazon",
            amount=Decimal("-151.00"),  # Wrong amount
            transaction_type="debit",
        )
        
        statement = BankStatementData(
            transactions=[extracted],
            check_images=[],
        )
        
        matches = matcher.match_statement_to_bank_feed(
            statement, sample_qbo_transactions
        )
        
        assert len(matches) == 1
        assert matches[0].qbo_match.matched == False
    
    def test_check_image_linking(self, matcher, sample_qbo_transactions):
        """Test that check images are linked to check transactions."""
        check_image = CheckData(
            check_number="1234",
            payee="ABC Corp",
            amount=Decimal("500.00"),
            date=date(2026, 1, 16),
            image_path="s3://bucket/check_1234.png",
        )
        
        extracted = BankTransaction(
            date=date(2026, 1, 16),
            description="Check 1234",
            amount=Decimal("-500.00"),
            transaction_type="check",
            check_number="1234",
        )
        
        statement = BankStatementData(
            transactions=[extracted],
            check_images=[check_image],
        )
        
        matches = matcher.match_statement_to_bank_feed(
            statement, sample_qbo_transactions
        )
        
        assert len(matches) == 1
        assert matches[0].extracted.check_image is not None
        assert matches[0].extracted.check_image.check_number == "1234"
    
    def test_match_summary(self, matcher, sample_qbo_transactions):
        """Test match summary statistics."""
        transactions = [
            BankTransaction(
                date=date(2026, 1, 15),
                description="Amazon",
                amount=Decimal("-150.00"),
                transaction_type="debit",
            ),
            BankTransaction(
                date=date(2026, 1, 20),
                description="Unknown",
                amount=Decimal("-999.99"),  # Won't match
                transaction_type="debit",
            ),
        ]
        
        statement = BankStatementData(
            transactions=transactions,
            check_images=[],
        )
        
        matches = matcher.match_statement_to_bank_feed(
            statement, sample_qbo_transactions
        )
        
        summary = matcher.get_match_summary(matches)
        
        assert summary["total_transactions"] == 2
        assert summary["matched"] == 1
        assert summary["unmatched"] == 1


class TestVendorMatcher:
    """Test vendor name matching."""
    
    @pytest.fixture
    def matcher(self):
        return VendorMatcher()
    
    @pytest.fixture
    def sample_vendors(self):
        return [
            {"id": "v1", "name": "Amazon"},
            {"id": "v2", "name": "Staples Office Supplies"},
            {"id": "v3", "name": "AT&T Wireless"},
        ]
    
    def test_exact_match(self, matcher, sample_vendors):
        """Test exact vendor name match."""
        vendor, score = matcher.find_or_suggest_vendor("Amazon", sample_vendors)
        
        assert vendor is not None
        assert vendor["id"] == "v1"
        assert score == 1.0
    
    def test_partial_match(self, matcher, sample_vendors):
        """Test partial vendor name match."""
        vendor, score = matcher.find_or_suggest_vendor("Staples", sample_vendors)
        
        assert vendor is not None
        assert vendor["id"] == "v2"
        assert score >= 0.7
    
    def test_no_match(self, matcher, sample_vendors):
        """Test when no vendor matches."""
        vendor, score = matcher.find_or_suggest_vendor("Completely Unknown Corp", sample_vendors)
        
        assert vendor is None
        assert score < 0.7
    
    def test_vendor_name_cleanup(self, matcher):
        """Test vendor name cleanup for creating new vendors."""
        assert matcher.suggest_vendor_name("AMAZON.COM LLC") == "Amazon.Com"
        assert matcher.suggest_vendor_name("staples inc") == "Staples"
        assert matcher.suggest_vendor_name("") == "Unknown Vendor"
