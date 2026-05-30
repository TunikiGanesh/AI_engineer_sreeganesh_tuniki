"""
Utility / helper functions shared across the project.
"""

import os
import tempfile
from pathlib import Path


def save_uploaded_file(uploaded_file) -> str:
    """
    Persist a Streamlit UploadedFile object to a temporary directory.

    Args:
        uploaded_file: streamlit.runtime.uploaded_file_manager.UploadedFile

    Returns:
        Absolute path to the saved temp file.

    Raises:
        ValueError: If the uploaded_file object is None or has no content.
    """
    if uploaded_file is None:
        raise ValueError("No file was provided to save.")

    suffix = Path(uploaded_file.name).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        return tmp.name


def detect_file_type(file_path: str) -> str:
    """
    Return a lowercase file-type string based on the file extension.

    Args:
        file_path: Path to the file.

    Returns:
        One of: 'pdf', 'csv', 'txt', or raises ValueError for unsupported types.
    """
    ext = Path(file_path).suffix.lower().lstrip(".")
    supported = {"pdf", "csv", "txt"}
    if ext not in supported:
        raise ValueError(
            f"Unsupported file type '.{ext}'. "
            f"Accepted formats: {', '.join(sorted(supported))}."
        )
    return ext


def cleanup_temp_file(file_path: str) -> None:
    """Silently remove a temporary file if it exists."""
    try:
        if file_path and os.path.isfile(file_path):
            os.remove(file_path)
    except OSError:
        pass  # Non-critical — temp file cleanup failure is acceptable


def format_field(value: object, fallback: str = "N/A") -> str:
    """
    Return a string representation of *value*, or *fallback* if None / empty.

    Args:
        value:    Any value that may be None or empty.
        fallback: Replacement string when value is absent.

    Returns:
        Cleaned string or the fallback.
    """
    if value is None:
        return fallback
    s = str(value).strip()
    return s if s else fallback
