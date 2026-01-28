"""
Receipt AI - Document processor for QuickBooks Online
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import documents, health, qbo

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

# Routes
app.include_router(health.router, tags=["Health"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(qbo.router, prefix="/api/qbo", tags=["QuickBooks"])


@app.get("/")
async def root():
    return {
        "name": "Receipt AI",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }
