"""
Bank Feed Matching Service

Matches extracted transactions from bank statements to QBO bank feed.
This is the KEY differentiator - auto-matching docs to transactions.
"""

from typing import List, Optional, Tuple
from datetime import date, timedelta
from decimal import Decimal
from dataclasses import dataclass
import difflib

from app.schemas.documents import (
    BankTransaction,
    BankStatementData,
    CheckData,
    QBOMatchResult,
    TransactionMatch,
)


@dataclass
class QBOBankTransaction:
    """Representation of a QBO bank feed transaction."""
    id: str
    date: date
    amount: Decimal
    description: str
    check_number: Optional[str] = None
    vendor_id: Optional[str] = None
    category_id: Optional[str] = None
    is_matched: bool = False
    has_attachment: bool = False


class BankFeedMatcher:
    """
    Matches extracted bank statement transactions to QBO bank feed.
    
    Matching logic:
    1. Amount must match exactly (required)
    2. Date should be within range (preferred)
    3. Check number must match for checks (if available)
    4. Description/vendor similarity (bonus)
    
    Score thresholds:
    - 90+: Auto-match (high confidence)
    - 70-89: Suggested match (review recommended)
    - <70: No match found
    """
    
    def __init__(
        self,
        date_tolerance_days: int = 5,
        auto_match_threshold: float = 90.0,
        suggest_match_threshold: float = 70.0,
    ):
        """
        Initialize matcher.
        
        Args:
            date_tolerance_days: How many days difference to allow
            auto_match_threshold: Score above which to auto-match
            suggest_match_threshold: Score above which to suggest match
        """
        self.date_tolerance_days = date_tolerance_days
        self.auto_match_threshold = auto_match_threshold
        self.suggest_match_threshold = suggest_match_threshold
    
    def match_statement_to_bank_feed(
        self,
        statement: BankStatementData,
        qbo_transactions: List[QBOBankTransaction],
    ) -> List[TransactionMatch]:
        """
        Match all transactions from a bank statement to QBO bank feed.
        
        Args:
            statement: Extracted bank statement data
            qbo_transactions: List of QBO bank feed transactions
            
        Returns:
            List of TransactionMatch with match results
        """
        results = []
        
        # Create a copy of QBO transactions we can mark as used
        available_qbo = list(qbo_transactions)
        
        for extracted_txn in statement.transactions:
            match_result = self._find_best_match(extracted_txn, available_qbo)
            
            # If matched, remove from available pool
            if match_result.matched and match_result.qbo_transaction_id:
                available_qbo = [
                    t for t in available_qbo 
                    if t.id != match_result.qbo_transaction_id
                ]
            
            # Link check image if this is a check transaction
            check_image = self._find_check_image(
                extracted_txn, 
                statement.check_images
            )
            if check_image:
                extracted_txn.check_image = check_image
            
            results.append(TransactionMatch(
                extracted=extracted_txn,
                qbo_match=match_result,
            ))
        
        return results
    
    def _find_best_match(
        self,
        extracted: BankTransaction,
        qbo_transactions: List[QBOBankTransaction],
    ) -> QBOMatchResult:
        """Find the best matching QBO transaction."""
        
        candidates = []
        
        for qbo_txn in qbo_transactions:
            score, reasons = self._calculate_match_score(extracted, qbo_txn)
            
            if score >= self.suggest_match_threshold:
                candidates.append((qbo_txn, score, reasons))
        
        if not candidates:
            return QBOMatchResult(
                matched=False,
                match_score=0.0,
                match_reasons=["No matching transaction found"],
            )
        
        # Sort by score, take best
        candidates.sort(key=lambda x: x[1], reverse=True)
        best_match, best_score, reasons = candidates[0]
        
        return QBOMatchResult(
            matched=best_score >= self.suggest_match_threshold,
            qbo_transaction_id=best_match.id,
            match_score=best_score,
            match_reasons=reasons,
        )
    
    def _calculate_match_score(
        self,
        extracted: BankTransaction,
        qbo: QBOBankTransaction,
    ) -> Tuple[float, List[str]]:
        """
        Calculate match score between extracted and QBO transaction.
        
        Returns (score, list of reasons)
        """
        score = 0.0
        reasons = []
        
        # Amount match (REQUIRED - must be exact)
        amount_diff = abs(float(extracted.amount) - float(qbo.amount))
        if amount_diff < 0.01:
            score += 40
            reasons.append(f"Amount matches: ${extracted.amount}")
        else:
            # No amount match = no match at all
            return 0.0, ["Amount does not match"]
        
        # Date match
        if extracted.date and qbo.date:
            date_diff = abs((extracted.date - qbo.date).days)
            
            if date_diff == 0:
                score += 30
                reasons.append("Date matches exactly")
            elif date_diff <= 1:
                score += 25
                reasons.append(f"Date within 1 day")
            elif date_diff <= 3:
                score += 20
                reasons.append(f"Date within 3 days")
            elif date_diff <= self.date_tolerance_days:
                score += 10
                reasons.append(f"Date within {date_diff} days")
            else:
                reasons.append(f"Date differs by {date_diff} days")
        
        # Check number match (very strong signal for checks)
        if extracted.check_number and qbo.check_number:
            if extracted.check_number == qbo.check_number:
                score += 25
                reasons.append(f"Check number matches: {extracted.check_number}")
            else:
                # Check numbers don't match - probably wrong transaction
                score -= 20
                reasons.append(f"Check numbers differ: {extracted.check_number} vs {qbo.check_number}")
        
        # Description/vendor similarity
        if extracted.description and qbo.description:
            similarity = self._string_similarity(
                extracted.description.lower(),
                qbo.description.lower()
            )
            
            if similarity > 0.8:
                score += 15
                reasons.append(f"Description highly similar ({similarity:.0%})")
            elif similarity > 0.5:
                score += 10
                reasons.append(f"Description somewhat similar ({similarity:.0%})")
            elif similarity > 0.3:
                score += 5
                reasons.append(f"Description loosely similar ({similarity:.0%})")
        
        # Vendor suggestion match
        if extracted.vendor_suggestion and qbo.description:
            vendor_similarity = self._string_similarity(
                extracted.vendor_suggestion.lower(),
                qbo.description.lower()
            )
            
            if vendor_similarity > 0.6:
                score += 10
                reasons.append(f"Vendor name matches description")
        
        # Transaction type consistency
        if extracted.transaction_type == "check" and qbo.check_number:
            score += 5
            reasons.append("Both identified as checks")
        
        return score, reasons
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity ratio."""
        return difflib.SequenceMatcher(None, s1, s2).ratio()
    
    def _find_check_image(
        self,
        transaction: BankTransaction,
        check_images: List[CheckData],
    ) -> Optional[CheckData]:
        """Find matching check image for a transaction."""
        
        if transaction.transaction_type != "check":
            return None
        
        if not transaction.check_number:
            return None
        
        for check in check_images:
            # Match by check number
            if check.check_number == transaction.check_number:
                return check
            
            # Match by amount if check number not available
            if check.amount and transaction.amount:
                if abs(float(check.amount) - abs(float(transaction.amount))) < 0.01:
                    # Also check date if available
                    if check.date and transaction.date:
                        if abs((check.date - transaction.date).days) <= 1:
                            return check
        
        return None
    
    def get_match_summary(
        self,
        matches: List[TransactionMatch],
    ) -> dict:
        """
        Get summary statistics for match results.
        """
        total = len(matches)
        matched = sum(1 for m in matches if m.qbo_match and m.qbo_match.matched)
        high_confidence = sum(
            1 for m in matches 
            if m.qbo_match and m.qbo_match.match_score >= self.auto_match_threshold
        )
        with_checks = sum(
            1 for m in matches 
            if m.extracted.check_image is not None
        )
        
        return {
            "total_transactions": total,
            "matched": matched,
            "unmatched": total - matched,
            "high_confidence_matches": high_confidence,
            "needs_review": matched - high_confidence,
            "transactions_with_check_images": with_checks,
            "match_rate": f"{(matched/total*100):.1f}%" if total > 0 else "0%",
        }


class VendorMatcher:
    """
    Matches extracted vendor names to QBO vendors.
    Creates new vendors when needed.
    """
    
    def __init__(self, similarity_threshold: float = 0.7):
        self.similarity_threshold = similarity_threshold
    
    def find_or_suggest_vendor(
        self,
        extracted_name: str,
        qbo_vendors: List[dict],
    ) -> Tuple[Optional[dict], float]:
        """
        Find best matching vendor or suggest creating new.
        
        Returns (vendor_dict or None, confidence_score)
        """
        if not extracted_name:
            return None, 0.0
        
        extracted_lower = extracted_name.lower().strip()
        best_match = None
        best_score = 0.0
        
        for vendor in qbo_vendors:
            vendor_name = vendor.get("name", "").lower()
            
            # Exact match
            if extracted_lower == vendor_name:
                return vendor, 1.0
            
            # Fuzzy match
            similarity = difflib.SequenceMatcher(
                None, extracted_lower, vendor_name
            ).ratio()
            
            if similarity > best_score:
                best_score = similarity
                best_match = vendor
            
            # Check if extracted name is contained in vendor name or vice versa
            if extracted_lower in vendor_name or vendor_name in extracted_lower:
                contained_score = 0.85
                if contained_score > best_score:
                    best_score = contained_score
                    best_match = vendor
        
        if best_score >= self.similarity_threshold:
            return best_match, best_score
        
        return None, best_score
    
    def suggest_vendor_name(self, extracted_name: str) -> str:
        """
        Clean up extracted vendor name for creating new vendor.
        """
        if not extracted_name:
            return "Unknown Vendor"
        
        # Basic cleanup
        name = extracted_name.strip()
        
        # Remove common suffixes
        suffixes_to_remove = [
            " LLC", " Inc", " Corp", " Co", " Ltd",
            " #", " -", " *",
        ]
        for suffix in suffixes_to_remove:
            if name.upper().endswith(suffix.upper()):
                name = name[:-len(suffix)]
        
        # Title case
        name = name.title()
        
        return name
