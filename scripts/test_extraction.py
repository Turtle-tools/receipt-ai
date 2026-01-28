#!/usr/bin/env python3
"""
Quick extraction test script.

Usage:
    python scripts/test_extraction.py path/to/receipt.pdf
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.extraction.extractor import DocumentExtractor
from app.core.config import settings


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_extraction.py <file_path>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    # Check API key
    if not settings.ai_api_key:
        print("Error: AI API key not configured")
        print("Set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env")
        sys.exit(1)
    
    print(f"📄 Extracting data from: {file_path.name}")
    print(f"🤖 Using: {settings.ai_provider} ({settings.ai_model})")
    print()
    
    # Read file
    with open(file_path, "rb") as f:
        file_data = f.read()
    
    # Extract
    extractor = DocumentExtractor()
    
    try:
        result = extractor.extract(
            file_data=file_data,
            file_type=file_path.suffix[1:],
        )
        
        print("✅ Extraction successful!")
        print()
        print("=" * 60)
        print(json.dumps(result, indent=2))
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
