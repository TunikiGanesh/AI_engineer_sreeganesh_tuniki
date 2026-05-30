"""
CSV / tabular-data parser using pandas.
Converts an uploaded CSV into a readable text block suitable for LLM ingestion.
"""

import pandas as pd
from pathlib import Path


def extract_text_from_csv(file_path: str) -> str:
    """
    Load a CSV file and convert it to a structured text representation.

    Strategy:
      1. Attempt comma-separated; fall back to tab-separated.
      2. Render column names, shape summary, and a full string table.
      3. Also emit a numeric-columns statistics block to give the LLM
         additional context on ranges / magnitudes.

    Args:
        file_path: Path to the CSV file.

    Returns:
        Human-readable text summary of the CSV content.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file cannot be parsed as tabular data.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    # Try common separators
    df: pd.DataFrame | None = None
    for sep in (",", ";", "\t", "|"):
        try:
            candidate = pd.read_csv(str(path), sep=sep, engine="python", on_bad_lines="skip")
            if candidate.shape[1] > 1:  # at least two columns → correct delimiter
                df = candidate
                break
        except Exception:
            continue

    if df is None:
        raise ValueError(f"Could not parse '{file_path}' as CSV with common separators.")

    # Clean up column names
    df.columns = [str(c).strip() for c in df.columns]

    lines: list[str] = []
    lines.append(f"=== CSV SUMMARY ===")
    lines.append(f"Rows: {df.shape[0]}  |  Columns: {df.shape[1]}")
    lines.append(f"Column names: {', '.join(df.columns.tolist())}")
    lines.append("")

    # Full data table (limit to first 200 rows for very large files)
    max_rows = 200
    preview_df = df.head(max_rows)
    lines.append("=== DATA TABLE ===")
    lines.append(preview_df.to_string(index=False, max_colwidth=60))

    if len(df) > max_rows:
        lines.append(f"... ({len(df) - max_rows} additional rows omitted)")

    # Numeric statistics block
    numeric_df = df.select_dtypes(include="number")
    if not numeric_df.empty:
        lines.append("")
        lines.append("=== NUMERIC STATISTICS ===")
        lines.append(numeric_df.describe().round(2).to_string())

    return "\n".join(lines)
