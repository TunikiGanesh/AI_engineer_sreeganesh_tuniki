"""
PDF report generator.
Populates the Jinja2 HTML template and converts it to PDF using WeasyPrint.
"""

import os
from ctypes.util import find_library
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from models.financial_model import ReportData


def _resolve_template_dir() -> str:
    """Return the absolute path to the templates/ directory."""
    here = Path(__file__).parent  # generator/
    return str(here.parent / "templates")


def render_html(report_data: ReportData, template_dir: str | None = None) -> str:
    """
    Render the Jinja2 HTML template with the supplied report data.

    Args:
        report_data:  Complete ReportData bundle.
        template_dir: Override path to the templates directory (optional).

    Returns:
        Rendered HTML string ready to be passed to WeasyPrint.
    """
    tdir = template_dir or _resolve_template_dir()
    env = Environment(loader=FileSystemLoader(tdir), autoescape=True)
    template = env.get_template("report_template.html")

    context = {
        "metrics": report_data.metrics,
        "commentary": report_data.commentary,
        "revenue_chart_path": report_data.revenue_chart_path,
        "ebitda_chart_path":  report_data.ebitda_chart_path,
        "pat_chart_path":     report_data.pat_chart_path,
        "report_date":        datetime.now().strftime("%B %Y"),
    }

    return template.render(**context)


def _paragraph(text: object, style: ParagraphStyle) -> Paragraph:
    """Create a ReportLab paragraph from arbitrary report text."""
    value = "N/A" if text is None else str(text)
    return Paragraph(value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), style)


def _build_reportlab_pdf(report_data: ReportData, pdf_path: str) -> None:
    """Generate a PDF without native GTK/Pango dependencies."""
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        textColor=colors.HexColor("#003366"),
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        spaceAfter=8,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        textColor=colors.HexColor("#6B7C93"),
        alignment=TA_CENTER,
        spaceAfter=14,
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#003366"),
        fontSize=12,
        leading=15,
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
        spaceAfter=6,
    )

    metrics = report_data.metrics
    commentary = report_data.commentary
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=12 * mm,
        bottomMargin=14 * mm,
        title=f"{metrics.company_name} Equity Research Report",
    )

    story = [
        _paragraph(f"{metrics.company_name}", title_style),
        _paragraph(f"{metrics.sector} | Equity Research | {datetime.now():%B %Y}", subtitle_style),
    ]

    valuation_rows = [
        ["Recommendation", metrics.recommendation, "Target Price", metrics.target_price],
        ["CMP", metrics.cmp, "Upside / Downside", metrics.upside_downside],
        ["Market Cap", metrics.market_cap, "Revenue", metrics.revenue],
    ]
    valuation_table = Table(valuation_rows, colWidths=[32 * mm, 43 * mm, 36 * mm, 43 * mm])
    valuation_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0F4F9")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1A1A2E")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D8E4EF")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([valuation_table, Spacer(1, 8)])

    sections = [
        ("Investment Thesis", commentary.investment_thesis),
        ("Business Overview", metrics.business_overview),
        ("Outlook & Valuation", f"{metrics.outlook}\n\n{commentary.outlook_valuation}"),
        ("Risk Factors", commentary.risk_factors),
    ]
    for heading, text in sections:
        story.extend([_paragraph(heading, heading_style), _paragraph(text, body_style)])

    if metrics.key_highlights:
        story.append(_paragraph("Key Highlights", heading_style))
        story.append(ListFlowable(
            [ListItem(_paragraph(item, body_style)) for item in metrics.key_highlights],
            bulletType="bullet",
            leftIndent=14,
        ))

    financial_rows = [
        ["Metric", "Value"],
        ["Revenue Growth", metrics.revenue_growth],
        ["EBITDA", metrics.ebitda],
        ["EBITDA Margin", metrics.ebitda_margin],
        ["PAT", metrics.pat],
        ["PAT Growth", metrics.pat_growth],
        ["EPS", metrics.eps],
        ["ROE", metrics.roe],
        ["Debt", metrics.debt],
    ]
    financial_table = Table(financial_rows, colWidths=[55 * mm, 95 * mm])
    financial_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D8E4EF")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFD")]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([_paragraph("Financial Snapshot", heading_style), financial_table])

    chart_paths = [
        report_data.revenue_chart_path,
        report_data.ebitda_chart_path,
        report_data.pat_chart_path,
    ]
    existing_charts = [path for path in chart_paths if path and os.path.exists(path)]
    if existing_charts:
        story.append(_paragraph("Financial Performance Charts", heading_style))
        for chart_path in existing_charts:
            story.append(Image(chart_path, width=155 * mm, height=83 * mm, kind="proportional"))
            story.append(Spacer(1, 5))

    story.extend([
        Spacer(1, 10),
        _paragraph(
            "Disclaimer: This report is for informational purposes only and does not constitute investment advice.",
            body_style,
        ),
    ])
    doc.build(story)


def _has_weasyprint_native_libs() -> bool:
    """Return whether WeasyPrint's native text libraries appear available."""
    if os.name != "nt":
        return True
    return find_library("gobject-2.0-0") is not None


def generate_pdf(
    report_data: ReportData,
    output_dir: str = "outputs",
    template_dir: str | None = None,
) -> str:
    """
    Generate a PDF equity research report from structured report data.

    Steps:
      1. Render Jinja2 template → HTML string
      2. Write a temporary HTML file (so WeasyPrint can resolve relative
         image paths via base_url)
      3. Convert HTML + CSS to PDF with WeasyPrint
      4. Return the absolute path to the generated PDF

    Args:
        report_data:  ReportData bundle containing metrics, commentary, chart paths.
        output_dir:   Directory to save the output PDF.
        template_dir: Optional override for template directory.

    Returns:
        Absolute path to the generated PDF file.

    Raises:
        RuntimeError: If PDF generation fails.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    tdir      = template_dir or _resolve_template_dir()
    css_path  = os.path.join(tdir, "report_style.css")

    # Render HTML
    html_string = render_html(report_data, template_dir=tdir)

    # Write temp HTML alongside templates so relative paths resolve
    tmp_html = os.path.join(tdir, "_report_tmp.html")
    with open(tmp_html, "w", encoding="utf-8") as fh:
        fh.write(html_string)

    # Output file name
    company_slug = (
        report_data.metrics.company_name
        .replace(" ", "_")
        .replace("/", "-")
        .lower()
    )
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_name   = f"{company_slug}_equity_report_{timestamp}.pdf"
    pdf_path   = os.path.abspath(os.path.join(output_dir, pdf_name))

    try:
        if not _has_weasyprint_native_libs():
            raise RuntimeError("WeasyPrint native GTK/Pango libraries are not installed.")

        from weasyprint import CSS, HTML

        html_doc = HTML(filename=tmp_html, base_url=tdir)
        css_doc  = CSS(filename=css_path)
        html_doc.write_pdf(pdf_path, stylesheets=[css_doc])
    except Exception as exc:
        try:
            _build_reportlab_pdf(report_data, pdf_path)
        except Exception as fallback_exc:
            raise RuntimeError(
                "PDF generation failed with WeasyPrint and ReportLab fallback. "
                f"WeasyPrint error: {exc}; fallback error: {fallback_exc}"
            ) from fallback_exc
    finally:
        # Clean up the temporary HTML file
        if os.path.exists(tmp_html):
            os.remove(tmp_html)

    return pdf_path
