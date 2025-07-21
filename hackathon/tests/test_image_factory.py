"""
Test image factory for Hackathon test suite
Utilities for creating test images to avoid duplication
"""

import io
from PIL import Image, ImageDraw
from typing import Tuple, Optional, Union

from .test_constants import (
    TEST_IMAGE_SIZE, TEST_IMAGE_COLOR, TEST_IMAGE_TEXT,
    SMALL_IMAGE_SIZE, MAX_IMAGE_SIZE_MB
)


def create_test_image(
    size: Tuple[int, int] = TEST_IMAGE_SIZE,
    color: str = TEST_IMAGE_COLOR,
    text: str = TEST_IMAGE_TEXT,
    format: str = 'PNG'
) -> io.BytesIO:
    """
    Create a test image with optional text
    
    Args:
        size: Image dimensions (width, height)
        color: Background color
        text: Text to draw on image
        format: Image format (PNG, JPEG, etc.)
    
    Returns:
        BytesIO object containing the image
    """
    img = Image.new('RGB', size, color=color)
    
    if text:
        try:
            draw = ImageDraw.Draw(img)
            # Try to center the text
            text_x = max(10, size[0] // 10)
            text_y = max(10, size[1] // 10)
            draw.text((text_x, text_y), text, fill='navy')
        except Exception:
            # If text drawing fails, continue without text
            pass
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format=format)
    img_bytes.seek(0)
    return img_bytes


def create_small_test_image(color: str = 'red') -> io.BytesIO:
    """Create small test image for quick tests"""
    return create_test_image(size=SMALL_IMAGE_SIZE, color=color, text="")


def create_large_test_image(
    size: Tuple[int, int] = (2000, 1500),
    color: str = 'blue'
) -> io.BytesIO:
    """Create large test image for size limit testing"""
    return create_test_image(size=size, color=color, text="Large Test Image")


def create_invalid_image_file() -> io.BytesIO:
    """Create invalid image file for negative testing"""
    invalid_content = b"This is not an image file"
    return io.BytesIO(invalid_content)


def create_test_image_with_transparency(
    size: Tuple[int, int] = TEST_IMAGE_SIZE,
    background_color: str = 'white'
) -> io.BytesIO:
    """Create test image with transparency (PNG format)"""
    img = Image.new('RGBA', size, color=background_color)
    draw = ImageDraw.Draw(img)
    
    # Add some transparent elements
    draw.rectangle([10, 10, 50, 50], fill=(255, 0, 0, 128))  # Semi-transparent red
    draw.ellipse([60, 60, 100, 100], fill=(0, 255, 0, 128))  # Semi-transparent green
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes


def create_test_jpeg_image(
    size: Tuple[int, int] = TEST_IMAGE_SIZE,
    quality: int = 85
) -> io.BytesIO:
    """Create test JPEG image with specified quality"""
    img = Image.new('RGB', size, color='lightcoral')
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), "JPEG Test Image", fill='darkred')
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=quality)
    img_bytes.seek(0)
    return img_bytes


def create_oversized_image(target_mb: float = MAX_IMAGE_SIZE_MB + 1) -> io.BytesIO:
    """
    Create an image that exceeds the size limit for testing
    
    Args:
        target_mb: Target size in megabytes
    
    Returns:
        BytesIO object containing oversized image
    """
    # Calculate dimensions to achieve target file size
    # This is approximate - actual file size depends on compression
    target_bytes = int(target_mb * 1024 * 1024)
    estimated_pixels = target_bytes // 3  # Rough estimate for RGB
    dimension = int(estimated_pixels ** 0.5)
    
    # Create large image
    img = Image.new('RGB', (dimension, dimension))
    
    # Add noise to prevent too much compression
    import random
    pixels = img.load()
    for i in range(dimension):
        for j in range(dimension):
            pixels[i, j] = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255)
            )
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes


def get_image_info(image_bytes: io.BytesIO) -> dict:
    """
    Get information about an image
    
    Args:
        image_bytes: Image as BytesIO object
    
    Returns:
        Dictionary with image information
    """
    image_bytes.seek(0)
    
    try:
        img = Image.open(image_bytes)
        info = {
            'format': img.format,
            'mode': img.mode,
            'size': img.size,
            'width': img.width,
            'height': img.height
        }
        
        # Get file size
        image_bytes.seek(0, 2)  # Seek to end
        file_size = image_bytes.tell()
        info['file_size_bytes'] = file_size
        info['file_size_mb'] = file_size / (1024 * 1024)
        
        image_bytes.seek(0)  # Reset position
        return info
        
    except Exception as e:
        return {'error': str(e)}


def create_test_image_files_dict(
    image_bytes: io.BytesIO,
    filename: str = "test_image.png"
) -> dict:
    """
    Create files dictionary for FastAPI file upload testing
    
    Args:
        image_bytes: Image as BytesIO object
        filename: Name for the uploaded file
    
    Returns:
        Dictionary suitable for FastAPI TestClient file upload
    """
    image_bytes.seek(0)
    return {
        "image": (filename, image_bytes, "image/png")
    }