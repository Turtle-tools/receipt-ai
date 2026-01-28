"""
PDF processing utilities.

Converts PDFs to images for AI vision model processing.
"""

import io
from typing import List, Tuple, Optional
from pathlib import Path


def pdf_to_images(
    pdf_data: bytes,
    dpi: int = 200,
    max_pages: Optional[int] = None,
) -> List[Tuple[bytes, Tuple[int, int]]]:
    """
    Convert PDF to list of images (one per page).
    
    Args:
        pdf_data: PDF file content as bytes
        dpi: Resolution for rendering (default 200)
        max_pages: Maximum pages to process (None for all)
        
    Returns:
        List of (image_bytes, (width, height)) tuples
    """
    try:
        from pdf2image import convert_from_bytes
        from PIL import Image
    except ImportError:
        raise ImportError(
            "pdf2image and Pillow required. Install with: "
            "pip install pdf2image Pillow"
        )
    
    # Convert PDF to PIL images
    pil_images = convert_from_bytes(
        pdf_data,
        dpi=dpi,
        first_page=1,
        last_page=max_pages,
    )
    
    results = []
    for img in pil_images:
        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()
        
        results.append((image_bytes, img.size))
    
    return results


def extract_page_as_image(
    pdf_data: bytes,
    page_number: int,
    dpi: int = 200,
) -> Tuple[bytes, Tuple[int, int]]:
    """
    Extract a single page from PDF as image.
    
    Args:
        pdf_data: PDF file content
        page_number: Page to extract (1-indexed)
        dpi: Resolution
        
    Returns:
        (image_bytes, (width, height))
    """
    from pdf2image import convert_from_bytes
    
    images = convert_from_bytes(
        pdf_data,
        dpi=dpi,
        first_page=page_number,
        last_page=page_number,
    )
    
    if not images:
        raise ValueError(f"Page {page_number} not found in PDF")
    
    img = images[0]
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    
    return buffer.getvalue(), img.size


def get_pdf_page_count(pdf_data: bytes) -> int:
    """Get number of pages in a PDF."""
    try:
        from pdf2image import pdfinfo_from_bytes
        info = pdfinfo_from_bytes(pdf_data)
        return info.get("Pages", 0)
    except Exception:
        # Fallback: try to convert and count
        from pdf2image import convert_from_bytes
        images = convert_from_bytes(pdf_data, dpi=72)  # Low DPI for speed
        return len(images)


def crop_region_from_pdf_page(
    pdf_data: bytes,
    page_number: int,
    x_percent: float,
    y_percent: float,
    width_percent: float,
    height_percent: float,
    dpi: int = 300,
) -> bytes:
    """
    Crop a region from a PDF page.
    
    Used for extracting check images from bank statements.
    
    Args:
        pdf_data: PDF content
        page_number: Page number (1-indexed)
        x_percent: Left edge as percentage of page width (0-100)
        y_percent: Top edge as percentage of page height (0-100)
        width_percent: Width as percentage (0-100)
        height_percent: Height as percentage (0-100)
        dpi: Resolution for extraction (higher = better quality)
        
    Returns:
        Cropped image as PNG bytes
    """
    from PIL import Image
    from pdf2image import convert_from_bytes
    
    # Get the page as image
    images = convert_from_bytes(
        pdf_data,
        dpi=dpi,
        first_page=page_number,
        last_page=page_number,
    )
    
    if not images:
        raise ValueError(f"Page {page_number} not found")
    
    img = images[0]
    width, height = img.size
    
    # Calculate pixel coordinates from percentages
    x = int(x_percent / 100 * width)
    y = int(y_percent / 100 * height)
    w = int(width_percent / 100 * width)
    h = int(height_percent / 100 * height)
    
    # Crop
    cropped = img.crop((x, y, x + w, y + h))
    
    # Convert to bytes
    buffer = io.BytesIO()
    cropped.save(buffer, format="PNG")
    
    return buffer.getvalue()


def is_pdf(data: bytes) -> bool:
    """Check if data is a PDF file."""
    return data[:4] == b'%PDF'


def is_image(data: bytes) -> bool:
    """Check if data is a common image format."""
    # PNG
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return True
    # JPEG
    if data[:2] == b'\xff\xd8':
        return True
    # GIF
    if data[:6] in (b'GIF87a', b'GIF89a'):
        return True
    return False


def get_image_dimensions(image_data: bytes) -> Tuple[int, int]:
    """Get dimensions of an image."""
    from PIL import Image
    
    img = Image.open(io.BytesIO(image_data))
    return img.size


def normalize_image(
    image_data: bytes,
    max_dimension: int = 2048,
    format: str = "PNG",
) -> bytes:
    """
    Normalize image for AI processing.
    
    - Resize if too large
    - Convert to consistent format
    - Ensure RGB mode
    """
    from PIL import Image
    
    img = Image.open(io.BytesIO(image_data))
    
    # Convert to RGB if needed (handles RGBA, grayscale, etc.)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    
    # Resize if too large
    width, height = img.size
    if max(width, height) > max_dimension:
        ratio = max_dimension / max(width, height)
        new_size = (int(width * ratio), int(height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    
    # Save to bytes
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    
    return buffer.getvalue()
