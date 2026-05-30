"""
Financial data models using Pydantic for type validation and serialization.
Defines the complete schema for equity research report data.
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class FinancialMetrics(BaseModel):
    """Core financial metrics extracted from the uploaded document."""

    company_name: str = Field(default="N/A", description="Company name")
    sector: str = Field(default="N/A", description="Business sector / industry")
    market_cap: str = Field(default="N/A", description="Market capitalization")
    cmp: str = Field(default="N/A", description="Current Market Price")
    target_price: str = Field(default="N/A", description="Analyst target price")
    recommendation: str = Field(default="BUY", description="BUY / HOLD / SELL")
    upside_downside: str = Field(default="N/A", description="Return % from CMP to target")

    # Income statement metrics
    revenue: str = Field(default="N/A", description="Total revenue (₹ Cr)")
    revenue_growth: str = Field(default="N/A", description="Revenue growth YoY %")
    ebitda: str = Field(default="N/A", description="EBITDA (₹ Cr)")
    ebitda_margin: str = Field(default="N/A", description="EBITDA margin %")
    pat: str = Field(default="N/A", description="Profit After Tax (₹ Cr)")
    pat_growth: str = Field(default="N/A", description="PAT growth YoY %")
    eps: str = Field(default="N/A", description="Earnings Per Share")
    roe: str = Field(default="N/A", description="Return on Equity %")
    debt: str = Field(default="N/A", description="Total Debt (₹ Cr)")

    # Narrative sections
    key_highlights: List[str] = Field(
        default_factory=list,
        description="Bullet-point key highlights"
    )
    business_overview: str = Field(
        default="N/A",
        description="Business description paragraph"
    )
    outlook: str = Field(
        default="N/A",
        description="Forward-looking commentary"
    )
    risks: List[str] = Field(
        default_factory=list,
        description="Key risk factors"
    )

    # Historical time-series for charts (3–5 years)
    revenue_series: List[float] = Field(
        default_factory=list,
        description="Historical revenue figures for charting"
    )
    ebitda_series: List[float] = Field(
        default_factory=list,
        description="Historical EBITDA figures for charting"
    )
    pat_series: List[float] = Field(
        default_factory=list,
        description="Historical PAT figures for charting"
    )
    years: List[str] = Field(
        default_factory=list,
        description="Fiscal years corresponding to series data"
    )


class AnalystCommentary(BaseModel):
    """Analyst-written commentary sections for the research report."""

    investment_thesis: str = Field(
        default="N/A",
        description="Core investment thesis paragraph"
    )
    key_highlights_commentary: str = Field(
        default="N/A",
        description="Narrative around key financial highlights"
    )
    outlook_valuation: str = Field(
        default="N/A",
        description="Outlook and valuation commentary"
    )
    risk_factors: str = Field(
        default="N/A",
        description="Detailed risk factor discussion"
    )


class ReportData(BaseModel):
    """Complete data bundle passed to the HTML/PDF report generator."""

    metrics: FinancialMetrics
    commentary: AnalystCommentary

    # Absolute paths to generated chart PNGs
    revenue_chart_path: str = Field(default="")
    ebitda_chart_path: str = Field(default="")
    pat_chart_path: str = Field(default="")
