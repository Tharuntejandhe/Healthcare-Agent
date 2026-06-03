import fitz  # PyMuPDF
import os
import re
import logging
from typing import List

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path: str) -> List[str]:
    """
    Extracts text lines from a PDF, filtering out common noise.
    Returns all non-empty lines that don't match exclusion patterns.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file at {file_path} does not exist.")

    # Header patterns to exclude (noise)
    EXCLUDE_PATTERNS = [
        re.compile(r'page \d+ of \d+', re.IGNORECASE),
        re.compile(r'report date', re.IGNORECASE),
        re.compile(r'physician', re.IGNORECASE),
        re.compile(r'patient info', re.IGNORECASE),
        re.compile(r'confidential', re.IGNORECASE)
    ]

    cleaned_lines = []

    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                text = page.get_text("text")
                lines = text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line or len(line) < 3:
                        continue
                        
                    if any(pattern.search(line) for pattern in EXCLUDE_PATTERNS):
                        continue
                    
                    # Normalize whitespace
                    normalized_line = re.sub(r'\s+', ' ', line)
                    cleaned_lines.append(normalized_line)

        return cleaned_lines

    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        raise Exception(f"Unexpected error: {str(e)}")
