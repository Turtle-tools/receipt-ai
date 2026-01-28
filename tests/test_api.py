"""
API endpoint tests.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_root(self):
        """Test root endpoint returns app info."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Receipt AI"
        assert data["status"] == "running"
        assert "version" in data
    
    def test_health(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"


class TestDocumentEndpoints:
    """Test document processing endpoints."""
    
    def test_upload_invalid_type(self):
        """Test that invalid file types are rejected."""
        # Create a fake text file
        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.txt", b"hello world", "text/plain")},
        )
        
        assert response.status_code == 400
        assert "not supported" in response.json()["detail"]
    
    def test_upload_valid_image(self):
        """Test uploading a valid image file."""
        # Create a minimal valid PNG (1x1 pixel)
        png_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00'
            b'\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00'
            b'\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        
        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.png", png_data, "image/png")},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["filename"] == "test.png"
        assert data["status"] == "uploaded"
    
    def test_get_nonexistent_document(self):
        """Test getting a document that doesn't exist."""
        response = client.get("/api/documents/doc_nonexistent")
        assert response.status_code == 404


class TestQBOEndpoints:
    """Test QuickBooks Online endpoints."""
    
    def test_qbo_status(self):
        """Test QBO connection status."""
        response = client.get("/api/qbo/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "connected" in data
        # Should be disconnected by default
        assert data["connected"] == False
    
    def test_qbo_connect_not_configured(self):
        """Test QBO connect when not configured."""
        response = client.get("/api/qbo/connect")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "not_implemented"
