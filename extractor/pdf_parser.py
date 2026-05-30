"""
PDF text extractor using PyMuPDF (fitz).
Extracts clean plain-text from every page of an uploaded PDF document.
"""

import fitz  # PyMuPDF
from pathlib import Path


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract all text content from a PDF file.

    Args:
        file_path: Absolute or relative path to the PDF file.

    Returns:
        Concatenated text from all pages, stripped of excessive whitespace.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file cannot be opened as a PDF.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    try:
        doc = fitz.open(str(path))
    except Exception as exc:
        raise ValueError(f"Unable to open PDF '{file_path}': {exc}") from exc

    pages_text: list[str] = []

    for page_num, page in enumerate(doc, start=1):
        try:
            text = page.get_text("text")  # plain-text mode
            if text.strip():
                pages_text.append(f"--- Page {page_num} ---\n{text.strip()}")
        except Exception as exc:
            # Log and skip unreadable pages rather than aborting
            pages_text.append(f"--- Page {page_num} [unreadable: {exc}] ---")

    doc.close()

    if not pages_text:
        raise ValueError("PDF appears to contain no extractable text (may be image-only).")

    return "\n\n".join(pages_text)
