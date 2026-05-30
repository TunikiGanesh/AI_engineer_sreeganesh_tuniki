"""
app.py — Geojit-Style Equity Research Report Generator
Main Streamlit application entry point.

Run:
    streamlit run app.py
"""

import os
import sys
import traceback
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# ── Ensure project root is on sys.path ──────────────────────────────────────
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ── Load .env for OPENAI_API_KEY ─────────────────────────────────────────────
load_dotenv(ROOT / ".env")

# ── Internal imports ──────────────────────────────────────────────────────────
from extractor.pdf_parser  import extract_text_from_pdf
from extractor.csv_parser  import extract_text_from_csv
from extractor.llm_extractor import (
    extract_financial_metrics,
    generate_analyst_commentary,
)
from charts.chart_generator import generate_all_charts
from generator.pdf_generator import generate_pdf
from models.financial_model  import ReportData
from utils.helpers           import save_uploaded_file, detect_file_type, cleanup_temp_file

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Equity Research Generator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS — Geojit-inspired dark-navy premium theme ─────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Source+Sans+3:wght@300;400;600&display=swap');

    /* ── Global ── */
    html, body, [class*="css"] {
        font-family: 'Source Sans 3', sans-serif;
    }

    /* ── App background ── */
    .stApp {
        background: linear-gradient(160deg, #0A1628 0%, #0D2044 50%, #0A1628 100%);
        min-height: 100vh;
    }

    /* ── Top banner ── */
    .top-banner {
        background: linear-gradient(90deg, #002855 0%, #003F7F 50%, #C8960C 100%);
        padding: 16px 32px;
        border-radius: 8px;
        margin-bottom: 24px;
        border-bottom: 3px solid #C8960C;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .top-banner h1 {
        font-family: 'Playfair Display', serif;
        color: #FFFFFF;
        font-size: 26px;
        font-weight: 700;
        margin: 0;
        letter-spacing: 0.5px;
    }
    .top-banner p {
        color: #A8C8E8;
        font-size: 13px;
        margin: 4px 0 0 0;
    }
    .banner-badge {
        background: rgba(200,150,12,0.3);
        border: 1px solid #C8960C;
        border-radius: 20px;
        padding: 4px 14px;
        color: #FFD580;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
    }

    /* ── Input panel card ── */
    .input-panel {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(200,150,12,0.3);
        border-radius: 10px;
        padding: 24px;
        backdrop-filter: blur(8px);
    }

    /* ── Input labels ── */
    .stTextInput label, .stFileUploader label {
        color: #A8C8E8 !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
    }

    /* ── Text input field ── */
    .stTextInput input {
        background: rgba(0, 30, 70, 0.8) !important;
        border: 1px solid rgba(200, 150, 12, 0.4) !important;
        border-radius: 6px !important;
        color: #FFFFFF !important;
        font-size: 15px !important;
        padding: 10px 14px !important;
    }
    .stTextInput input:focus {
        border-color: #C8960C !important;
        box-shadow: 0 0 0 2px rgba(200,150,12,0.25) !important;
    }

    /* ── File uploader ── */
    [data-testid="stFileUploadDropzone"] {
        background: rgba(0, 30, 70, 0.6) !important;
        border: 2px dashed rgba(200, 150, 12, 0.5) !important;
        border-radius: 8px !important;
        color: #A8C8E8 !important;
    }

    /* ── Generate button ── */
    .stButton > button {
        background: linear-gradient(135deg, #C8960C 0%, #E6B020 100%) !important;
        color: #002855 !important;
        font-weight: 800 !important;
        font-size: 14px !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 12px 36px !important;
        width: 100% !important;
        margin-top: 8px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 20px rgba(200,150,12,0.4) !important;
    }
    .stButton > button:hover {
        box-shadow: 0 6px 28px rgba(200,150,12,0.6) !important;
        transform: translateY(-1px) !important;
    }

    /* ── Download button ── */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #1A7A4A 0%, #22A064 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 28px !important;
        box-shadow: 0 4px 16px rgba(26,122,74,0.4) !important;
    }

    /* ── Status cards ── */
    .status-card {
        background: rgba(0,50,102,0.6);
        border: 1px solid rgba(200,150,12,0.3);
        border-left: 4px solid #C8960C;
        border-radius: 6px;
        padding: 14px 18px;
        margin: 12px 0;
        color: #FFFFFF;
        font-size: 14px;
    }

    /* ── Metric cards ── */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin: 16px 0;
    }
    .metric-card {
        background: rgba(0,40,80,0.7);
        border: 1px solid rgba(200,150,12,0.25);
        border-radius: 8px;
        padding: 14px;
        text-align: center;
    }
    .metric-label {
        color: #7090B0;
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }
    .metric-value {
        color: #FFD580;
        font-size: 16px;
        font-weight: 700;
    }

    /* ── Section titles ── */
    .section-title {
        font-family: 'Playfair Display', serif;
        color: #C8960C;
        font-size: 18px;
        font-weight: 700;
        border-bottom: 1px solid rgba(200,150,12,0.3);
        padding-bottom: 6px;
        margin: 20px 0 14px 0;
    }

    /* ── Success / Error alerts ── */
    .stSuccess, .stError, .stWarning, .stInfo {
        border-radius: 8px !important;
    }

    /* ── Progress bar ── */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #C8960C, #FFD580) !important;
    }

    /* ── Divider ── */
    hr { border-color: rgba(200,150,12,0.25) !important; }

    /* ── Hide default header/footer ── */
    #MainMenu { visibility: hidden; }
    header    { visibility: hidden; }
    footer    { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ═════════════════════════════════════════════════════════════════════════════
# TOP BANNER
# ═════════════════════════════════════════════════════════════════════════════
st.markdown(
    """
    <div class="top-banner">
      <div>
        <h1>📊 Equity Research Report Generator</h1>
        <p>AI-powered • Geojit-style • Institutional Grade</p>
      </div>
      <div class="banner-badge">Powered by GPT-4o</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ═════════════════════════════════════════════════════════════════════════════
# TWO-COLUMN LAYOUT
# ═════════════════════════════════════════════════════════════════════════════
left_col, right_col = st.columns([1, 1.6], gap="large")

# ──────────────────────────────────────────────────────────────────────────────
# LEFT: Input Panel
# ──────────────────────────────────────────────────────────────────────────────
with left_col:
    st.markdown("<div class='input-panel'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Report Configuration</div>", unsafe_allow_html=True)

    company_name = st.text_input(
        "Company Name",
        placeholder="e.g. Infosys Limited",
        help="Enter the company name as it appears in the document.",
    )

    uploaded_file = st.file_uploader(
        "Financial Context Document",
        type=["pdf", "csv", "txt"],
        help="Upload the annual report, earnings release, or financial data file.",
    )

    # API key (optional override — can also use .env)
    api_key_input = st.text_input(
        "OpenAI API Key (optional — uses .env if blank)",
        type="password",
        placeholder="sk-...",
    )
    if api_key_input.strip():
        os.environ["OPENAI_API_KEY"] = api_key_input.strip()

    st.markdown("---")

    generate_btn = st.button("⚡ Generate Research Report", use_container_width=True)

    st.markdown(
        """
        <div style='margin-top:18px; color:#5A7A9A; font-size:11px; line-height:1.6;'>
        <strong style='color:#C8960C;'>Accepted Inputs</strong><br>
        📄 PDF — Annual reports, earnings releases<br>
        📊 CSV — Financial data tables<br>
        📝 TXT — Plain-text financial summaries
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# RIGHT: Results Panel
# ──────────────────────────────────────────────────────────────────────────────
with right_col:
    st.markdown("<div class='section-title'>Report Output</div>", unsafe_allow_html=True)

    if not generate_btn:
        st.markdown(
            """
            <div style='
                background: rgba(0,40,80,0.4);
                border: 2px dashed rgba(200,150,12,0.2);
                border-radius: 10px;
                padding: 48px 24px;
                text-align: center;
                color: #4A6A8A;
            '>
                <div style='font-size:42px; margin-bottom:12px;'>📊</div>
                <div style='font-family:"Playfair Display",serif; font-size:18px;
                            color:#C8960C; margin-bottom:8px;'>
                    Awaiting Report Generation
                </div>
                <div style='font-size:13px; line-height:1.7;'>
                    Enter a company name, upload a financial document,<br>
                    then click <strong style='color:#FFD580;'>Generate Research Report</strong>.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # GENERATION PIPELINE
    # ──────────────────────────────────────────────────────────────────────────
    if generate_btn:
        # ── Validation ───────────────────────────────────────────────────────
        errors = []
        if not company_name.strip():
            errors.append("Company name is required.")
        if uploaded_file is None:
            errors.append("Please upload a financial document (PDF, CSV, or TXT).")
        if not os.getenv("OPENAI_API_KEY", "").strip():
            errors.append("OpenAI API key not found. Set it in .env or the input above.")

        if errors:
            for err in errors:
                st.error(f"⚠️ {err}")
            st.stop()

        # ── Pipeline ─────────────────────────────────────────────────────────
        tmp_file_path: str = ""
        try:
            progress = st.progress(0, text="Initialising pipeline…")

            # Step 1 — Save uploaded file
            progress.progress(10, text="📥  Saving uploaded document…")
            tmp_file_path = save_uploaded_file(uploaded_file)
            file_type     = detect_file_type(tmp_file_path)

            # Step 2 — Extract text
            progress.progress(25, text=f"🔍  Extracting text from {file_type.upper()}…")
            if file_type == "pdf":
                raw_text = extract_text_from_pdf(tmp_file_path)
            elif file_type == "csv":
                raw_text = extract_text_from_csv(tmp_file_path)
            else:  # txt
                with open(tmp_file_path, "r", encoding="utf-8", errors="ignore") as fh:
                    raw_text = fh.read()

            if not raw_text.strip():
                st.error("❌ The uploaded file appears to be empty or unreadable.")
                st.stop()

            # Step 3 — LLM extraction
            progress.progress(45, text="🤖  Extracting financial metrics via GPT-4o…")
            metrics = extract_financial_metrics(raw_text, company_name_hint=company_name.strip())

            # Step 4 — Commentary generation
            progress.progress(62, text="✍️  Generating analyst commentary…")
            commentary = generate_analyst_commentary(metrics)

            # Step 5 — Charts
            progress.progress(76, text="📈  Generating financial charts…")
            outputs_dir = str(ROOT / "outputs")
            chart_paths = generate_all_charts(metrics, output_dir=outputs_dir)

            # Step 6 — Build ReportData and generate PDF
            progress.progress(88, text="📄  Assembling & rendering PDF…")
            report_data = ReportData(
                metrics=metrics,
                commentary=commentary,
                revenue_chart_path=chart_paths.get("revenue", ""),
                ebitda_chart_path=chart_paths.get("ebitda", ""),
                pat_chart_path=chart_paths.get("pat", ""),
            )
            pdf_path = generate_pdf(report_data, output_dir=outputs_dir)
            progress.progress(100, text="✅  Report generated successfully!")

            # ── Display extracted metrics ─────────────────────────────────────
            st.success("✅ Research report generated successfully!")

            st.markdown(
                f"""
                <div class='metric-grid'>
                  <div class='metric-card'>
                    <div class='metric-label'>Company</div>
                    <div class='metric-value' style='font-size:13px;'>
                        {metrics.company_name}
                    </div>
                  </div>
                  <div class='metric-card'>
                    <div class='metric-label'>Recommendation</div>
                    <div class='metric-value'>{metrics.recommendation}</div>
                  </div>
                  <div class='metric-card'>
                    <div class='metric-label'>Target Price</div>
                    <div class='metric-value'>{metrics.target_price}</div>
                  </div>
                  <div class='metric-card'>
                    <div class='metric-label'>CMP</div>
                    <div class='metric-value'>{metrics.cmp}</div>
                  </div>
                  <div class='metric-card'>
                    <div class='metric-label'>Upside</div>
                    <div class='metric-value'>{metrics.upside_downside}</div>
                  </div>
                  <div class='metric-card'>
                    <div class='metric-label'>Sector</div>
                    <div class='metric-value' style='font-size:12px;'>
                        {metrics.sector}
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Financial snapshot table
            st.markdown("<div class='section-title'>Financial Snapshot</div>",
                        unsafe_allow_html=True)

            import pandas as pd
            snapshot_df = pd.DataFrame(
                {
                    "Metric": [
                        "Revenue", "Revenue Growth", "EBITDA", "EBITDA Margin",
                        "PAT", "PAT Growth", "EPS", "ROE", "Debt", "Market Cap",
                    ],
                    "Value": [
                        metrics.revenue, metrics.revenue_growth,
                        metrics.ebitda,  metrics.ebitda_margin,
                        metrics.pat,     metrics.pat_growth,
                        metrics.eps,     metrics.roe,
                        metrics.debt,    metrics.market_cap,
                    ],
                }
            )
            st.dataframe(snapshot_df, hide_index=True, use_container_width=True)

            # Key Highlights
            if metrics.key_highlights:
                st.markdown("<div class='section-title'>Key Highlights</div>",
                            unsafe_allow_html=True)
                for hl in metrics.key_highlights:
                    st.markdown(f"• {hl}")

            # Download button
            st.markdown("<br>", unsafe_allow_html=True)
            with open(pdf_path, "rb") as pdf_fh:
                pdf_bytes = pdf_fh.read()

            company_slug = metrics.company_name.replace(" ", "_").lower()
            st.download_button(
                label="⬇️  Download Equity Research Report (PDF)",
                data=pdf_bytes,
                file_name=f"{company_slug}_equity_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

            st.markdown(
                f"<div style='color:#5A7A9A; font-size:11px; margin-top:8px; text-align:center;'>"
                f"PDF saved to: <code>{pdf_path}</code></div>",
                unsafe_allow_html=True,
            )

        except EnvironmentError as exc:
            st.error(f"🔑 API Key Error: {exc}")
        except ValueError as exc:
            st.error(f"📋 Data Error: {exc}")
        except RuntimeError as exc:
            st.error(f"⚙️ Generation Error: {exc}")
        except Exception:
            st.error("An unexpected error occurred. See details below.")
            st.code(traceback.format_exc(), language="text")
        finally:
            cleanup_temp_file(tmp_file_path)
