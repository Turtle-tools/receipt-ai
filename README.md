# Receipt AI 🧾

AI-powered receipt and document processor for QuickBooks Online.

**Upload receipts, invoices, bank statements → AI extracts data → Push to QBO**

## Features (MVP)

- 📷 Upload receipts, invoices, bills (PDF, image, email)
- 🤖 AI extracts: vendor, amount, date, category, line items
- ✏️ Review & edit extracted data
- 🔄 Push to QuickBooks Online as expense or bill
- 📊 Simple dashboard

## Why This Exists

Current solutions like Dext/Receipt Bank charge $31-62/company/month.
We're building a modern alternative at **$10/month**.

## Tech Stack

- **Backend:** Python (FastAPI)
- **AI:** OpenAI GPT-4o / Claude for extraction
- **Storage:** S3/Cloudflare R2
- **Database:** PostgreSQL
- **Frontend:** React/Next.js (later)
- **Integration:** QuickBooks Online API

## Getting Started

```bash
# Clone
git clone https://github.com/Turtle-tools/receipt-ai.git
cd receipt-ai

# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run
python -m uvicorn app.main:app --reload
```

## Project Structure

```
receipt-ai/
├── app/
│   ├── main.py          # FastAPI app
│   ├── api/             # API routes
│   ├── core/            # Config, security
│   ├── models/          # Database models
│   ├── services/        # Business logic
│   │   ├── extraction/  # AI document extraction
│   │   ├── qbo/         # QuickBooks integration
│   │   └── storage/     # File storage
│   └── schemas/         # Pydantic schemas
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

## Roadmap

- [x] Repository setup
- [ ] Basic FastAPI skeleton
- [ ] Document upload endpoint
- [ ] AI extraction service (GPT-4o)
- [ ] QBO OAuth integration
- [ ] Push to QBO endpoint
- [ ] Simple web UI
- [ ] User authentication
- [ ] Stripe billing

## License

MIT

---

**Built by [Turtle-tools](https://github.com/Turtle-tools)** 🐢
