# Receipt AI 🧾

**AI-powered document processor for QuickBooks Online.**

Not just receipts — bank statements, checks, invoices, bills. Extract everything. Match to QBO bank feed. Attach source documents automatically.

## 🚀 Features

### Document Processing
- 📷 **Multi-format support:** PDF, PNG, JPG, HEIC
- 🏦 **Bank statement processing:** Extract ALL transactions
- 💳 **Check image extraction:** Snip checks from bank statements
- 🧾 **Receipt/Invoice OCR:** Vendor, amount, date, line items

### QBO Integration
- 🔄 **Bank feed matching:** Auto-match extracted transactions
- 📎 **Document attachment:** Attach source docs to transactions
- 👤 **Vendor management:** Auto-create or match vendors
- 📊 **Smart categorization:** Based on vendor history

### Why This Exists

| Feature | Dext | Hubdoc | Receipt AI |
|---------|------|--------|------------|
| Receipt capture | ✅ | ✅ | ✅ |
| Bank statement processing | ❌ | ❌ | ✅ |
| Check image extraction | ❌ | ❌ | ✅ |
| Bank feed matching | ❌ | ❌ | ✅ |
| Doc attachment to txns | ❌ | ❌ | ✅ |
| Price | $31-62/mo | $20/mo | **$10/mo** |

## 📦 Installation

```bash
# Clone
git clone https://github.com/Turtle-tools/receipt-ai.git
cd receipt-ai

# Setup virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
make install
# or: pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run
make run
# or: python -m uvicorn app.main:app --reload
```

## 🛠️ CLI Usage

```bash
# Classify a document
python cli.py classify receipt.jpg

# Extract data from a receipt
python cli.py extract receipt.jpg

# Extract from bank statement
python cli.py extract statement.pdf --type bank_statement

# Extract as JSON (for scripting)
python cli.py extract receipt.jpg --json

# Run the API server
python cli.py server --port 8000 --reload
```

## 🐳 Docker

```bash
# Build
make docker-build
# or: docker build -t receipt-ai .

# Run with docker-compose (includes PostgreSQL)
docker-compose up -d

# Run standalone
docker run -p 8000:8000 --env-file .env receipt-ai
```

## 📡 API Endpoints

### Documents
- `POST /api/documents/upload` - Upload document for processing
- `GET /api/documents/{id}` - Get document status
- `POST /api/documents/{id}/extract` - Trigger AI extraction
- `GET /api/documents/{id}/extracted` - Get extracted data
- `POST /api/documents/{id}/match-to-qbo` - Match to QBO bank feed
- `POST /api/documents/{id}/push-to-qbo` - Push to QuickBooks

### QuickBooks
- `GET /api/qbo/connect` - Start OAuth flow
- `GET /api/qbo/callback` - OAuth callback
- `GET /api/qbo/status` - Connection status
- `GET /api/qbo/accounts` - Get chart of accounts
- `GET /api/qbo/vendors` - Get vendor list

### Health
- `GET /` - App info
- `GET /health` - Health check

## 🏗️ Project Structure

```
receipt-ai/
├── app/
│   ├── main.py              # FastAPI application
│   ├── api/                 # API endpoints
│   │   ├── documents.py     # Document processing
│   │   ├── qbo.py          # QuickBooks integration
│   │   └── health.py       # Health checks
│   ├── core/
│   │   └── config.py       # Configuration
│   ├── schemas/
│   │   └── documents.py    # Data models
│   └── services/
│       ├── extraction/      # AI document extraction
│       │   └── extractor.py
│       ├── matching/        # Bank feed matching
│       │   └── matcher.py
│       ├── qbo/            # QuickBooks API client
│       │   └── client.py
│       └── storage/        # File storage
│           └── storage.py
├── tests/                  # Test suite
├── cli.py                  # Command-line interface
├── Dockerfile             # Container build
├── docker-compose.yml     # Local dev environment
├── Makefile              # Common commands
├── PRODUCT-SPEC.md       # Full product specification
├── requirements.txt
└── .env.example
```

## 🧪 Testing

```bash
# Run all tests
make test
# or: python -m pytest tests/ -v

# With coverage
python -m pytest tests/ -v --cov=app
```

## ⚙️ Configuration

Key environment variables (see `.env.example`):

```bash
# AI (required)
OPENAI_API_KEY=sk-...      # or ANTHROPIC_API_KEY

# QuickBooks (for QBO integration)
QBO_CLIENT_ID=...
QBO_CLIENT_SECRET=...
QBO_REDIRECT_URI=http://localhost:8000/api/qbo/callback

# Storage (optional, defaults to local)
STORAGE_TYPE=local         # local, s3, or r2
S3_BUCKET=my-bucket
```

## 🗺️ Roadmap

- [x] FastAPI skeleton
- [x] Document upload & classification
- [x] AI extraction (GPT-4o/Claude)
- [x] Bank statement transaction extraction
- [x] Check image snipping
- [x] Bank feed matching service
- [x] QBO API client
- [x] Storage service (local/S3/R2)
- [x] CLI tool
- [x] Docker support
- [x] Test suite
- [ ] QBO OAuth integration (needs API keys)
- [ ] Web UI
- [ ] User authentication
- [ ] Stripe billing
- [ ] Production deployment

## 📄 License

MIT

---

**Built by [Turtle-tools](https://github.com/Turtle-tools)** 🐢

*Slow and steady wins the race.*
