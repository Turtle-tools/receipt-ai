#!/usr/bin/env python3
"""
Receipt AI CLI - Test document extraction locally.

Usage:
    python cli.py extract receipt.jpg
    python cli.py extract bank-statement.pdf --type bank_statement
    python cli.py classify document.pdf
"""

import argparse
import json
import os
import sys
from pathlib import Path


def get_extractor():
    """Initialize AI extractor."""
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable")
        sys.exit(1)
    
    provider = "openai" if os.getenv("OPENAI_API_KEY") else "anthropic"
    
    from app.services.extraction.extractor import DocumentExtractor
    return DocumentExtractor(api_key=api_key, provider=provider)


def cmd_classify(args):
    """Classify a document."""
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    extractor = get_extractor()
    
    with open(file_path, "rb") as f:
        content = f.read()
    
    print(f"Classifying: {file_path.name}")
    doc_type = extractor.classify_document(content)
    
    print(f"\nDocument Type: {doc_type.value}")


def cmd_extract(args):
    """Extract data from a document."""
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    extractor = get_extractor()
    
    with open(file_path, "rb") as f:
        content = f.read()
    
    # Determine document type
    if args.type:
        from app.schemas.documents import DocumentType
        doc_type = DocumentType(args.type)
    else:
        print(f"Classifying: {file_path.name}")
        doc_type = extractor.classify_document(content)
        print(f"Detected type: {doc_type.value}")
    
    print(f"\nExtracting data...")
    
    # Extract based on type
    from app.schemas.documents import DocumentType
    
    if doc_type in [DocumentType.RECEIPT, DocumentType.INVOICE, DocumentType.BILL]:
        result = extractor.extract_receipt(content)
    elif doc_type == DocumentType.BANK_STATEMENT:
        # For now, treat as single page
        result = extractor.extract_bank_statement([content])
    elif doc_type == DocumentType.CHECK:
        result = extractor.extract_check(content)
    else:
        print(f"Unsupported document type: {doc_type}")
        sys.exit(1)
    
    # Output
    if args.json:
        print(json.dumps(result.model_dump(), indent=2, default=str))
    else:
        print("\n" + "=" * 50)
        print("EXTRACTED DATA")
        print("=" * 50)
        
        data = result.model_dump()
        for key, value in data.items():
            if value is not None and key != "raw_text":
                if isinstance(value, list):
                    print(f"\n{key}:")
                    for item in value[:10]:  # Limit to first 10
                        print(f"  - {item}")
                    if len(value) > 10:
                        print(f"  ... and {len(value) - 10} more")
                else:
                    print(f"{key}: {value}")


def cmd_server(args):
    """Run the API server."""
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Receipt AI - Document processor for QuickBooks Online"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # classify command
    classify_parser = subparsers.add_parser("classify", help="Classify a document")
    classify_parser.add_argument("file", help="Path to document file")
    classify_parser.set_defaults(func=cmd_classify)
    
    # extract command
    extract_parser = subparsers.add_parser("extract", help="Extract data from a document")
    extract_parser.add_argument("file", help="Path to document file")
    extract_parser.add_argument(
        "--type", "-t",
        choices=["receipt", "invoice", "bill", "bank_statement", "check"],
        help="Document type (auto-detected if not specified)"
    )
    extract_parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON"
    )
    extract_parser.set_defaults(func=cmd_extract)
    
    # server command
    server_parser = subparsers.add_parser("server", help="Run the API server")
    server_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    server_parser.add_argument("--port", "-p", type=int, default=8000, help="Port to listen on")
    server_parser.add_argument("--reload", "-r", action="store_true", help="Enable auto-reload")
    server_parser.set_defaults(func=cmd_server)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
