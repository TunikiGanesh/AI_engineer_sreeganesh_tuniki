# 📊 Equity Research Report Generator

A production-ready, AI-powered financial research report generator that creates **Geojit-style equity research PDFs** from uploaded financial documents.

---

## 🎯 What It Does

| Step | Action |
|------|--------|
| 1 | Accept a **company name** and a financial document (PDF, CSV, or TXT) |
| 2 | **Extract** all text / tabular data from the document |
| 3 | Send extracted content to **GPT-4o** for structured metric extraction |
| 4 | Generate **professional analyst commentary** (investment thesis, outlook, risks) |
| 5 | Produce **Revenue, EBITDA, and PAT bar charts** |
| 6 | Populate a **Geojit-style Jinja2 HTML template** |
| 7 | Convert to a **downloadable PDF** via WeasyPrint |

---

## 🗂 Project Structure

```
project/
├── app.py                     ← Streamlit entry point
├── requirements.txt
├── README.md
├── .env                       ← OPENAI_API_KEY goes here
│
├── extractor/
│   ├── pdf_parser.py          ← PyMuPDF text extraction
│   ├── csv_parser.py          ← Pandas CSV extraction
│   └── llm_extractor.py       ← GPT-4o metric + commentary generation
│
├── models/
│   └── financial_model.py     ← Pydantic schemas
│
├── charts/
│   └── chart_generator.py     ← Matplotlib bar charts
│
├── templates/
│   ├── report_template.html   ← Jinja2 HTML template
│   └── report_style.css       ← Geojit-style CSS
│
├── generator/
│   └── pdf_generator.py       ← Jinja2 + WeasyPrint PDF builder
│
├── outputs/                   ← Auto-created; PDFs & charts saved here
│
└── utils/
    └── helpers.py             ← Shared utilities
```

---

## ⚙️ Setup & Installation

### 1. Prerequisites

- Python **3.11+**
- `pip` (or `uv`)
- An **OpenAI API key** (GPT-4o access required)

> **System dependencies for WeasyPrint** — install once:
>
> ```bash
> # Ubuntu / Debian
> sudo apt-get install -y libpango-1.0-0 libpangocairo-1.0-0 libcairo2 \
>                         libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
>
> # macOS (Homebrew)
> brew install pango cairo gdk-pixbuf libffi
>
> # Windows — install GTK3 runtime from:
> # https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
> ```

### 2. Install Python dependencies

```bash
cd project
pip install -r requirements.txt
```

### 3. Configure API key

Create a `.env` file in the `project/` root:

```dotenv
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Alternatively, paste the key directly in the Streamlit sidebar at runtime.

---

## 🚀 Running the Application

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 📋 Using the App

1. **Company Name** — type the company name (e.g. `Infosys Limited`).
2. **Upload Document** — drag-and-drop or browse for a PDF, CSV, or TXT file.
3. **OpenAI API Key** — enter if not set in `.env`.
4. Click **⚡ Generate Research Report**.
5. Review the extracted metrics on screen.
6. Click **⬇️ Download Equity Research Report (PDF)** to save.

---

## 📄 Extracted Fields

| Category | Fields |
|----------|--------|
| **Identification** | Company Name, Sector, Market Cap |
| **Pricing** | CMP, Target Price, Recommendation, Upside % |
| **Income** | Revenue, Revenue Growth, EBITDA, EBITDA Margin, PAT, PAT Growth |
| **Per-share** | EPS, ROE |
| **Balance Sheet** | Debt |
| **Narrative** | Key Highlights, Business Overview, Outlook, Risks |
| **Time-series** | Revenue / EBITDA / PAT series + Fiscal Year labels |

---

## 🏗 Architecture Notes

### Document Parsing
- **PDF** → `fitz.Document.get_text("text")` (PyMuPDF page-by-page)
- **CSV** → pandas auto-delimiter detection + full table + stats block
- **TXT** → direct `open()` read

### LLM Extraction (GPT-4o)
- System prompt instructs model to return **pure JSON** matching the `FinancialMetrics` Pydantic schema.
- Response is sanitised (markdown fences stripped) before `json.loads()`.
- First 12,000 characters of document text are sent (context window safety).

### Commentary Generation (GPT-4o)
- Separate call with analyst-persona system prompt.
- Returns JSON with four keys: `investment_thesis`, `key_highlights_commentary`, `outlook_valuation`, `risk_factors`.

### Chart Generation (Matplotlib)
- Three bar charts: Revenue / EBITDA / PAT trends.
- Saved as PNG to `outputs/` with navy/gold Geojit colour palette.

### PDF Generation (WeasyPrint)
- Jinja2 renders HTML template with all metrics and absolute image paths.
- WeasyPrint converts HTML + CSS to A4 PDF (`@page` rule).

---

## 🔧 Error Handling

| Scenario | Behaviour |
|----------|-----------|
| Missing company name | Validation error shown |
| Empty file upload | Validation error shown |
| Unsupported file type | `ValueError` caught, shown in UI |
| Image-only PDF | `ValueError` with explanation |
| Missing API key | `EnvironmentError` caught, shown in UI |
| LLM returns invalid JSON | `ValueError` with raw LLM output preview |
| WeasyPrint failure | `RuntimeError` caught, shown in UI |
| Any other exception | Full traceback shown in UI |

Missing individual fields default to `"N/A"` per the Pydantic model defaults.

---

## 🧩 Extending the Project

- **Add more chart types** → edit `chart_generator.py` and update the template.
- **Add more extracted fields** → extend `FinancialMetrics` in `financial_model.py` and update the extraction prompt in `llm_extractor.py`.
- **Change report branding** → edit `report_style.css` and `report_template.html`.
- **Support XLSX input** → add an `xlsx_parser.py` using `openpyxl` or `pandas.read_excel`.

---

## 📜 Disclaimer

This tool generates research reports for informational purposes only. Output should not be construed as investment advice. Always consult a SEBI-registered investment advisor before making investment decisions.

---

*Built with ❤️ using Streamlit · OpenAI GPT-4o · PyMuPDF · Matplotlib · WeasyPrint*
