"""
OCR Service for CAPTCHA extraction using Tesseract
"""

import pytesseract
from PIL import Image
import re


def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from an image using Tesseract OCR.

    Args:
        image_path: Path to the image file

    Returns:
        Extracted text as a string
    """
    try:
        # Open the image file
        image = Image.open(image_path)
        
        # Use Tesseract to extract text
        # Using config for better results with CAPTCHA
        custom_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        extracted_text = pytesseract.image_to_string(image, config=custom_config)
        
        # Clean the extracted text
        cleaned_text = re.sub(r'[^a-zA-Z0-9]', '', extracted_text).strip()
        
        return cleaned_text
    
    except Exception as e:
        print(f"[!] Error extracting text from image: {e}")
        return ""


def is_valid_captcha(text: str, min_length: int = 4, max_length: int = 8) -> bool:
    """
    Validate if the extracted text is a valid CAPTCHA.

    Args:
        text: The text to validate
        min_length: Minimum acceptable length for CAPTCHA
        max_length: Maximum acceptable length for CAPTCHA

    Returns:
        True if text is valid, False otherwise
    """
    if not text:
        return False
    
    # Check length constraints
    if not (min_length <= len(text) <= max_length):
        return False
    
    # Check if text contains only alphanumeric characters
    if not re.match(r'^[a-zA-Z0-9]+$', text):
        return False
    
    return True


def process_captcha(image_path: str, min_length: int = 4, max_length: int = 8) -> dict:
    """
    Process a CAPTCHA image: extract text and validate it.

    Args:
        image_path: Path to the CAPTCHA image
        min_length: Minimum acceptable length for CAPTCHA
        max_length: Maximum acceptable length for CAPTCHA

    Returns:
        Dictionary containing:
        - 'text': extracted text (empty string if error)
        - 'is_valid': boolean indicating if text is valid
        - 'message': status message
    """
    extracted_text = extract_text_from_image(image_path)
    is_valid = is_valid_captcha(extracted_text, min_length, max_length)
    
    if not extracted_text:
        return {
            'text': '',
            'is_valid': False,
            'message': 'Failed to extract text from image'
        }
    
    if is_valid:
        return {
            'text': extracted_text,
            'is_valid': True,
            'message': f'Valid CAPTCHA text extracted: {extracted_text}'
        }
    else:
        return {
            'text': extracted_text,
            'is_valid': False,
            'message': f'Extracted text is invalid: {extracted_text} (length: {len(extracted_text)})'
        }


if __name__ == "__main__":
    # Example usage
    result = process_captcha("captcha.png")
    print(result)
