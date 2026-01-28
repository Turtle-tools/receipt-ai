"""
Receipt AI - Document processor for QuickBooks Online
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.api import documents, health, qbo, webhooks, analytics, batch

app = FastAPI(
    title="Receipt AI",
    description="AI-powered receipt and document processor for QuickBooks Online",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Routes
app.include_router(health.router, tags=["Health"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(batch.router, prefix="/api/batch", tags=["Batch Processing"])
app.include_router(qbo.router, prefix="/api/qbo", tags=["QuickBooks"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the web UI."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "name": "Receipt AI",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }
