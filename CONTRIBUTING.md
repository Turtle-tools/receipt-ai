# Contributing to Receipt AI

Thanks for your interest in contributing! This guide will help you get started.

---

## Development Setup

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 16+ (or use Docker)
- Redis 7+ (or use Docker)

### Quick Start

1. **Clone the repo:**
   ```bash
   git clone https://github.com/Turtle-tools/receipt-ai.git
   cd receipt-ai
   ```

2. **Copy environment file:**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

3. **Option A: Docker (easiest)**
   ```bash
   docker-compose up
   ```

4. **Option B: Local development**
   ```bash
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Start services (separate terminals)
   uvicorn app.main:app --reload
   celery -A app.tasks worker --loglevel=info
   ```

5. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

6. **Open your browser:**
   - Web UI: http://localhost:8000
   - API docs: http://localhost:8000/docs

---

## Project Structure

```
receipt-ai/
├── app/
│   ├── api/              # API endpoints
│   │   ├── documents.py  # Document upload/processing
│   │   ├── qbo.py        # QuickBooks integration
│   │   └── health.py     # Health checks
│   ├── core/             # Core configuration
│   │   ├── config.py     # Settings
│   │   └── database.py   # Database session
│   ├── models/           # Database models
│   │   └── database.py
│   ├── schemas/          # Pydantic schemas
│   │   └── documents.py
│   ├── services/         # Business logic
│   │   ├── extraction/   # AI extraction
│   │   ├── matching/     # Bank feed matching
│   │   ├── qbo/          # QuickBooks client
│   │   └── storage/      # File storage
│   ├── tasks/            # Celery background tasks
│   ├── templates/        # HTML templates
│   └── main.py           # FastAPI app
├── migrations/           # Alembic migrations
├── tests/                # Test suite
├── scripts/              # Helper scripts
├── docker-compose.yml    # Local development
├── Dockerfile            # Container image
├── requirements.txt      # Python dependencies
└── README.md            # Documentation
```

---

## Development Workflow

### 1. Create a feature branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make your changes

Follow these guidelines:
- Write clear, descriptive commit messages
- Add tests for new features
- Update documentation as needed
- Follow PEP 8 style guide

### 3. Test your changes

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Type checking
mypy app/

# Linting
ruff check app/
black app/ --check
```

### 4. Push and create a PR

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

---

## Code Style

We use:
- **Black** for code formatting (line length 100)
- **Ruff** for fast linting
- **mypy** for type checking
- **isort** for import sorting

Run all formatters:
```bash
make format
```

---

## Testing

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_extraction.py

# With coverage
pytest --cov=app

# Fast mode (skip slow tests)
pytest -m "not slow"
```

### Writing Tests

We use pytest. Example:

```python
def test_extract_receipt():
    extractor = DocumentExtractor()
    result = extractor.extract_receipt(sample_image)
    
    assert result["vendor"] == "Acme Corp"
    assert result["total"] == 42.99
```

---

## Database Migrations

We use Alembic for database migrations.

### Create a migration

```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "Add user table"

# Manual migration
alembic revision -m "Add custom index"
```

### Apply migrations

```bash
# Upgrade to latest
alembic upgrade head

# Rollback one version
alembic downgrade -1

# Show current version
alembic current
```

---

## Background Tasks

We use Celery for async processing.

### Adding a new task

```python
# app/tasks/your_module.py
from app.tasks import celery_app

@celery_app.task(name="your_task")
def your_task(arg1: str) -> dict:
    # Do work
    return {"status": "success"}
```

### Running tasks

```python
# Async (recommended)
result = your_task.delay(arg1="value")

# Blocking (for testing)
result = your_task.apply(args=["value"])
```

### Monitor tasks

```bash
# Celery flower (web UI)
celery -A app.tasks flower

# CLI monitoring
celery -A app.tasks inspect active
```

---

## AI Integration

### Supported Providers

- OpenAI (GPT-4o, GPT-4o-mini)
- Anthropic (Claude 3.5 Sonnet)

### Adding a new extraction type

1. Define schema in `app/schemas/documents.py`
2. Add extraction logic in `app/services/extraction/extractor.py`
3. Create task in `app/tasks/extraction.py`
4. Add API endpoint in `app/api/documents.py`
5. Write tests

---

## QuickBooks Integration

### OAuth Flow

1. User clicks "Connect QuickBooks"
2. Redirect to Intuit OAuth URL
3. User authorizes
4. Intuit redirects to `/api/qbo/callback`
5. Exchange code for tokens
6. Store tokens (encrypted)

### Testing with Sandbox

1. Create developer account at https://developer.intuit.com
2. Create a sandbox company
3. Get sandbox credentials
4. Set `QBO_ENVIRONMENT=sandbox` in .env

---

## Deployment

### Environment Variables

Required in production:
- `APP_ENV=production`
- `SECRET_KEY` (generate with `openssl rand -hex 32`)
- `DATABASE_URL`
- `REDIS_URL`
- AI provider API key (OpenAI or Anthropic)
- QuickBooks OAuth credentials
- Storage credentials (S3/R2)

### Docker Deployment

```bash
# Build image
docker build -t receipt-ai .

# Run
docker run -p 8000:8000 \
  -e DATABASE_URL=... \
  -e REDIS_URL=... \
  receipt-ai
```

### Scaling

- Run multiple API workers behind load balancer
- Scale Celery workers horizontally
- Use managed PostgreSQL (RDS, Supabase)
- Use managed Redis (ElastiCache, Upstash)

---

## Common Tasks

### Add a new AI provider

1. Add credentials to `app/core/config.py`
2. Create client in `app/services/extraction/`
3. Add provider option to `AI_PROVIDER` enum
4. Update extraction logic to support new provider

### Add a new document type

1. Add type to `DocumentType` enum
2. Create Pydantic schema
3. Add extraction prompt
4. Update QBO push logic
5. Add tests

### Debug extraction issues

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Test extraction directly
python cli.py extract path/to/document.pdf

# View extraction in API
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@receipt.pdf"
```

---

## Getting Help

- **Issues:** [GitHub Issues](https://github.com/Turtle-tools/receipt-ai/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Turtle-tools/receipt-ai/discussions)
- **Email:** support@ironcladcas.com

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

**Thank you for contributing!** 🎉
