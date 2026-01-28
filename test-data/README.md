# Test Data for Receipt AI

This directory contains realistic test data for validating document extraction.

## Bank Statements

The `bank-statements/` directory contains HTML mockups of real bank statement formats:

- **Chase Bank** - Business checking with check images
- Wells Fargo - (coming soon)
- Bank of America - (coming soon)
- Citibank - (coming soon)

### Features

✅ Realistic transaction data
✅ Check images (both handwritten & typed styles)
✅ Proper formatting matching real bank statements
✅ Multiple vendors and payment types
✅ Balance calculations

### Converting to PDF

To test PDF extraction, convert HTML to PDF:

```bash
# Option 1: Print from browser
# Open chase_statement.html in browser and print to PDF

# Option 2: Install wkhtmltopdf
sudo apt-get install wkhtmltopdf
wkhtmltopdf chase_statement.html chase_statement.pdf

# Option 3: Use Python with playwright
cd test-data
python convert_to_pdf.py
```

### Testing Extraction

```bash
# Test extraction on a statement
cd /home/ubuntu/clawd/projects/receipt-ai
python scripts/test_extraction.py test-data/bank-statements/chase_statement.pdf

# Or upload via API
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@test-data/bank-statements/chase_statement.pdf"
```

## Check Images

Check images include:
- Handwritten payee names (cursive font simulation)
- Typed payee names (Courier font)
- Realistic amounts and dates
- MICR line at bottom
- Signature lines

## Generating More Test Data

```bash
cd test-data
python generate_bank_statements.py
```

This will create additional statements with randomized:
- Transaction dates
- Amounts
- Vendors
- Check numbers
