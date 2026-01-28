#!/usr/bin/env python3
"""
Convert HTML bank statements to PDF using Playwright.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


async def html_to_pdf(html_path: Path, pdf_path: Path):
    """Convert HTML file to PDF."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Load HTML
        await page.goto(f"file://{html_path.absolute()}")
        
        # Wait for page to load
        await page.wait_for_load_state("networkidle")
        
        # Generate PDF
        await page.pdf(
            path=str(pdf_path),
            format="Letter",
            print_background=True,
            margin={
                "top": "0.5in",
                "right": "0.5in",
                "bottom": "0.5in",
                "left": "0.5in",
            }
        )
        
        await browser.close()
        
        print(f"✓ Created: {pdf_path}")


async def main():
    """Convert all HTML statements to PDF."""
    test_data_dir = Path(__file__).parent
    statements_dir = test_data_dir / "bank-statements"
    
    if not statements_dir.exists():
        print("Error: bank-statements directory not found")
        print("Run generate_bank_statements.py first")
        return
    
    # Convert all HTML files
    for html_file in statements_dir.glob("*.html"):
        pdf_file = html_file.with_suffix(".pdf")
        print(f"Converting {html_file.name}...")
        await html_to_pdf(html_file, pdf_file)
    
    print("\nAll statements converted to PDF!")


if __name__ == "__main__":
    asyncio.run(main())
