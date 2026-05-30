"""
LLM-powered extraction and commentary generator using OpenAI GPT-4o.

Two public functions:
  - extract_financial_metrics()  → FinancialMetrics (structured JSON extraction)
  - generate_analyst_commentary() → AnalystCommentary (narrative generation)
"""

import json
import os
import re
from typing import Any

from openai import OpenAI

from models.financial_model import AnalystCommentary, FinancialMetrics

# ---------------------------------------------------------------------------
# Client initialisation
# ---------------------------------------------------------------------------

def _get_client() -> OpenAI:
    """Return an OpenAI client, reading the API key from the environment."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. Add it to your .env file or environment."
        )
    return OpenAI(api_key=api_key)


# ---------------------------------------------------------------------------
# Extraction prompt
# ---------------------------------------------------------------------------

EXTRACTION_SYSTEM_PROMPT = """\
You are a senior equity research analyst specialising in Indian capital markets.
Your task is to extract structured financial data from the supplied document text
and return it as a single valid JSON object — nothing else, no markdown fences.

If a field cannot be found in the document, set its value to "N/A".
For list fields (key_highlights, risks, revenue_series, ebitda_series,
pat_series, years), return an empty array [] if data is unavailable.

JSON schema (all fields required):
{
  "company_name": "string",
  "sector": "string",
  "market_cap": "string  (e.g. ₹12,345 Cr)",
  "cmp": "string  (e.g. ₹1,234)",
  "target_price": "string  (e.g. ₹1,500)",
  "recommendation": "BUY | HOLD | SELL",
  "upside_downside": "string  (e.g. +21.5%)",
  "revenue": "string  (most recent FY, e.g. ₹8,921 Cr)",
  "revenue_growth": "string  (e.g. 14.3%)",
  "ebitda": "string  (e.g. ₹2,100 Cr)",
  "ebitda_margin": "string  (e.g. 23.5%)",
  "pat": "string  (e.g. ₹1,450 Cr)",
  "pat_growth": "string  (e.g. 18.2%)",
  "eps": "string  (e.g. ₹45.6)",
  "roe": "string  (e.g. 22.4%)",
  "debt": "string  (e.g. ₹3,200 Cr)",
  "key_highlights": ["string", ...],
  "business_overview": "string (2-3 sentences)",
  "outlook": "string (2-3 sentences)",
  "risks": ["string", ...],
  "revenue_series": [number, ...],
  "ebitda_series": [number, ...],
  "pat_series": [number, ...],
  "years": ["FY21", "FY22", ...]
}
"""

def _safe_json_parse(raw: str) -> dict[str, Any]:
    """
    Strip markdown code fences (```json ... ```) and parse JSON.
    Raises ValueError on failure.
    """
    cleaned = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM returned invalid JSON: {exc}\n\nRaw output:\n{raw[:500]}") from exc


# ---------------------------------------------------------------------------
# Public: extract financial metrics
# ---------------------------------------------------------------------------

def extract_financial_metrics(
    document_text: str,
    company_name_hint: str = "",
) -> FinancialMetrics:
    """
    Call GPT-4o to extract structured financial metrics from raw document text.

    Args:
        document_text:     Plain text extracted from the uploaded document.
        company_name_hint: Company name entered by the user (optional override).

    Returns:
        Validated FinancialMetrics Pydantic model.
    """
    client = _get_client()

    user_content = (
        f"Company name hint: {company_name_hint or 'unknown'}\n\n"
        f"Document text:\n{document_text[:12000]}"  # stay within context window
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user",   "content": user_content},
        ],
        temperature=0.1,
        max_tokens=2000,
    )

    raw_json = response.choices[0].message.content or ""
    data = _safe_json_parse(raw_json)

    # Override company name with user-provided value if extraction missed it
    if company_name_hint and (not data.get("company_name") or data["company_name"] == "N/A"):
        data["company_name"] = company_name_hint

    return FinancialMetrics(**data)


# ---------------------------------------------------------------------------
# Public: generate analyst commentary
# ---------------------------------------------------------------------------

COMMENTARY_SYSTEM_PROMPT = """\
You are a senior equity research analyst at a leading Indian brokerage.
Write professional, confident, data-driven commentary in the style of
Geojit, Motilal Oswal, or ICICI Securities research reports.
Keep each section concise (3–5 sentences) and actionable.
"""

def generate_analyst_commentary(metrics: FinancialMetrics) -> AnalystCommentary:
    """
    Generate four analyst commentary sections using GPT-4o.

    Args:
        metrics: Extracted FinancialMetrics model.

    Returns:
        AnalystCommentary with investment_thesis, key_highlights_commentary,
        outlook_valuation, and risk_factors.
    """
    client = _get_client()

    metrics_summary = (
        f"Company: {metrics.company_name} | Sector: {metrics.sector}\n"
        f"Revenue: {metrics.revenue} (growth {metrics.revenue_growth})\n"
        f"EBITDA: {metrics.ebitda} ({metrics.ebitda_margin} margin)\n"
        f"PAT: {metrics.pat} (growth {metrics.pat_growth})\n"
        f"EPS: {metrics.eps} | ROE: {metrics.roe} | Debt: {metrics.debt}\n"
        f"CMP: {metrics.cmp} | Target: {metrics.target_price} "
        f"| Recommendation: {metrics.recommendation}\n"
        f"Key highlights: {'; '.join(metrics.key_highlights[:5])}\n"
        f"Business overview: {metrics.business_overview}\n"
        f"Outlook: {metrics.outlook}\n"
        f"Risks: {'; '.join(metrics.risks[:5])}"
    )

    commentary_prompt = f"""\
Based on the following financial data, write four commentary sections.
Return a JSON object with exactly these keys:
  - investment_thesis
  - key_highlights_commentary
  - outlook_valuation
  - risk_factors

Financial data:
{metrics_summary}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": COMMENTARY_SYSTEM_PROMPT},
            {"role": "user",   "content": commentary_prompt},
        ],
        temperature=0.4,
        max_tokens=1500,
    )

    raw_json = response.choices[0].message.content or ""
    data = _safe_json_parse(raw_json)

    return AnalystCommentary(**data)
