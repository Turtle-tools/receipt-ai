#!/usr/bin/env python3
"""
Generate realistic bank statement mockups for testing.

Creates PDFs with:
- Major bank formats (Chase, Wells Fargo, BofA, Citi)
- Check images (handwritten & typed)
- Realistic transactions
- Proper formatting
"""

import random
from datetime import datetime, timedelta
from pathlib import Path

# Sample vendors for check payments
VENDORS = [
    "ABC Office Supplies",
    "Metro Property Management",
    "Johnson Electrical Services",
    "City Water & Sewer",
    "Tech Solutions LLC",
    "Green Landscaping Co",
    "Professional Cleaning Services",
    "Smith & Associates Law",
    "National Insurance Group",
    "Valley Equipment Rental",
]

# Transaction types
TRANSACTION_TYPES = [
    "ACH Credit",
    "Check",
    "Debit Card",
    "Wire Transfer",
    "Online Transfer",
    "ATM Withdrawal",
]


def generate_chase_statement_html():
    """Generate Chase Bank statement HTML."""
    
    html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page { size: letter; margin: 0.5in; }
        body { font-family: Arial, sans-serif; font-size: 10pt; color: #000; }
        .header { background: #0c2f54; color: white; padding: 20px; margin-bottom: 20px; }
        .logo { font-size: 24pt; font-weight: bold; }
        .account-info { margin: 20px 0; }
        .account-info table { width: 100%; border-collapse: collapse; }
        .account-info td { padding: 5px; border-bottom: 1px solid #ddd; }
        .section-title { background: #0c2f54; color: white; padding: 8px; font-weight: bold; margin-top: 20px; }
        .transactions table { width: 100%; border-collapse: collapse; font-size: 9pt; }
        .transactions th { background: #f0f0f0; padding: 8px; text-align: left; border-bottom: 2px solid #0c2f54; }
        .transactions td { padding: 6px; border-bottom: 1px solid #ddd; }
        .amount { text-align: right; }
        .check-image { margin: 10px 0; padding: 10px; border: 1px solid #ccc; background: #fafafa; }
        .check { border: 2px solid #000; padding: 20px; background: white; position: relative; }
        .check-number { position: absolute; top: 10px; right: 20px; font-family: 'Courier New', monospace; }
        .payee { margin-top: 30px; border-bottom: 1px solid #000; padding-bottom: 2px; }
        .amount-words { margin-top: 10px; font-size: 11pt; }
        .signature { margin-top: 40px; border-top: 1px solid #000; width: 200px; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">CHASE</div>
        <div>Business Banking</div>
    </div>
    
    <div class="account-info">
        <table>
            <tr>
                <td><strong>Account Holder:</strong> IronClad CAS LLC</td>
                <td><strong>Account Number:</strong> ****3421</td>
            </tr>
            <tr>
                <td><strong>Statement Period:</strong> December 1 - December 31, 2025</td>
                <td><strong>Business Checking</strong></td>
            </tr>
        </table>
    </div>
    
    <div class="section-title">ACCOUNT SUMMARY</div>
    <table style="width: 100%; margin: 10px 0;">
        <tr>
            <td>Beginning Balance (12/01/2025)</td>
            <td class="amount">$15,247.82</td>
        </tr>
        <tr>
            <td>Total Deposits and Credits</td>
            <td class="amount">$28,450.00</td>
        </tr>
        <tr>
            <td>Total Withdrawals and Debits</td>
            <td class="amount">$22,891.45</td>
        </tr>
        <tr style="border-top: 2px solid #000; font-weight: bold;">
            <td>Ending Balance (12/31/2025)</td>
            <td class="amount">$20,806.37</td>
        </tr>
    </table>
    
    <div class="section-title">TRANSACTION DETAILS</div>
    <div class="transactions">
        <table>
            <tr>
                <th>Date</th>
                <th>Description</th>
                <th>Check #</th>
                <th class="amount">Withdrawals</th>
                <th class="amount">Deposits</th>
                <th class="amount">Balance</th>
            </tr>
"""
    
    # Generate transactions
    balance = 15247.82
    start_date = datetime(2025, 12, 1)
    
    transactions = []
    
    # Add some deposits
    for i in range(5):
        date = start_date + timedelta(days=random.randint(1, 30))
        amount = random.uniform(2000, 8000)
        transactions.append({
            'date': date,
            'desc': 'ACH Credit - Customer Payment',
            'check': '',
            'withdrawal': '',
            'deposit': f"${amount:,.2f}",
            'amount': amount
        })
    
    # Add check payments
    check_numbers = [1001, 1002, 1003, 1004, 1005]
    for check_num in check_numbers:
        date = start_date + timedelta(days=random.randint(1, 30))
        amount = random.uniform(500, 3000)
        vendor = random.choice(VENDORS)
        transactions.append({
            'date': date,
            'desc': f'Check - {vendor}',
            'check': str(check_num),
            'withdrawal': f"${amount:,.2f}",
            'deposit': '',
            'amount': -amount
        })
    
    # Sort by date
    transactions.sort(key=lambda x: x['date'])
    
    for trans in transactions:
        balance += trans['amount']
        html += f"""
            <tr>
                <td>{trans['date'].strftime('%m/%d/%Y')}</td>
                <td>{trans['desc']}</td>
                <td>{trans['check']}</td>
                <td class="amount">{trans['withdrawal']}</td>
                <td class="amount">{trans['deposit']}</td>
                <td class="amount">${balance:,.2f}</td>
            </tr>
"""
    
    html += """
        </table>
    </div>
    
    <div class="section-title">CHECK IMAGES</div>
"""
    
    # Add check images
    for check_num in check_numbers:
        vendor = random.choice(VENDORS)
        amount = random.uniform(500, 3000)
        date = start_date + timedelta(days=random.randint(1, 30))
        
        # Alternate between handwritten and typed
        if check_num % 2 == 0:
            # Handwritten style
            payee_style = 'font-family: cursive; font-size: 14pt;'
            amount_style = 'font-family: cursive;'
        else:
            # Typed style
            payee_style = 'font-family: "Courier New", monospace;'
            amount_style = 'font-family: "Courier New", monospace;'
        
        html += f"""
    <div class="check-image">
        <strong>Check #{check_num}</strong>
        <div class="check">
            <div class="check-number">#{check_num}</div>
            <div style="margin-top: 10px;">
                <strong>IRONCLAD CAS LLC</strong><br>
                123 Business Way<br>
                New York, NY 10001
            </div>
            <div style="margin-top: 20px;">
                Date: <span style="{amount_style}">{date.strftime('%m/%d/%Y')}</span>
            </div>
            <div class="payee">
                Pay to the Order of: <span style="{payee_style}">{vendor}</span>
            </div>
            <div style="margin-top: 10px; text-align: right;">
                <strong style="{amount_style}">${amount:,.2f}</strong>
            </div>
            <div class="amount-words" style="{payee_style}">
                {amount_to_words(amount)} and {int((amount % 1) * 100)}/100 DOLLARS
            </div>
            <div style="margin-top: 20px; display: flex; justify-content: space-between;">
                <div>
                    <strong>CHASE</strong><br>
                    For: <span style="border-bottom: 1px solid #000; padding: 0 50px;">Office Supplies</span>
                </div>
                <div class="signature" style="{payee_style}">
                    Lee Johnson
                </div>
            </div>
            <div style="margin-top: 20px; font-family: 'Courier New', monospace; font-size: 8pt;">
                :054001204: 123456789: {check_num}
            </div>
        </div>
    </div>
"""
    
    html += """
    <div style="margin-top: 40px; font-size: 8pt; color: #666; text-align: center;">
        Member FDIC | Equal Housing Lender<br>
        For questions about your account, call 1-800-935-9935
    </div>
</body>
</html>
"""
    
    return html


def amount_to_words(amount):
    """Convert amount to words (simplified)."""
    ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine']
    teens = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen']
    tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
    
    num = int(amount)
    
    if num == 0:
        return 'Zero'
    
    if num < 10:
        return ones[num]
    elif num < 20:
        return teens[num - 10]
    elif num < 100:
        return tens[num // 10] + (' ' + ones[num % 10] if num % 10 else '')
    elif num < 1000:
        return ones[num // 100] + ' Hundred' + (' ' + amount_to_words(num % 100) if num % 100 else '')
    elif num < 1000000:
        return amount_to_words(num // 1000) + ' Thousand' + (' ' + amount_to_words(num % 1000) if num % 1000 else '')
    else:
        return str(num)


def main():
    """Generate all bank statement mockups."""
    
    # Create output directory
    output_dir = Path(__file__).parent / "bank-statements"
    output_dir.mkdir(exist_ok=True)
    
    # Generate Chase statement
    print("Generating Chase Bank statement...")
    chase_html = generate_chase_statement_html()
    
    with open(output_dir / "chase_statement.html", "w") as f:
        f.write(chase_html)
    
    print(f"✓ Created: {output_dir}/chase_statement.html")
    print("\nTo convert to PDF, you can:")
    print("  1. Open in browser and print to PDF")
    print("  2. Use wkhtmltopdf: wkhtmltopdf chase_statement.html chase_statement.pdf")
    print("  3. Use playwright: python convert_to_pdf.py")


if __name__ == "__main__":
    main()
