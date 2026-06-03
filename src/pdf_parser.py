"""
PDF Parser: Extracts and preprocesses text from corporate annual/sustainability reports.
Handles multi-column layouts, tables, and section detection.
"""

import re
import logging
from pathlib import Path
from typing import Optional
import pdfplumber
from pypdf import PdfReader

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Section header patterns (common in annual reports)
# ---------------------------------------------------------------------------
SECTION_HEADER_RE = re.compile(
    r"^(.*?(sustainability|environmental|social|governance|esg|climate|"
    r"responsibility|csr|community|diversity|ethics|compliance|"
    r"human rights|supply chain|energy|carbon|emissions|water|waste).*)$",
    re.IGNORECASE | re.MULTILINE,
)


class ReportPage:
    """Represents a single parsed page with metadata."""

    def __init__(self, page_num: int, text: str, section_hint: str = ""):
        self.page_num = page_num
        self.text = text
        self.section_hint = section_hint
        self.word_count = len(text.split())

    def __repr__(self):
        return f"<ReportPage {self.page_num}: {self.word_count} words>"


class ParsedReport:
    """Full parsed report with per-page content and aggregated text."""

    def __init__(self, path: str):
        self.path = path
        self.filename = Path(path).name
        self.pages: list[ReportPage] = []
        self.metadata: dict = {}
        self.total_pages: int = 0
        self.esg_page_indices: list[int] = []  # pages likely about ESG

    @property
    def full_text(self) -> str:
        return "\n".join(p.text for p in self.pages)

    @property
    def esg_focused_text(self) -> str:
        """Returns text from ESG-relevant pages only (for focused scoring)."""
        if self.esg_page_indices:
            return "\n".join(self.pages[i].text for i in self.esg_page_indices
                             if i < len(self.pages))
        return self.full_text

    @property
    def word_count(self) -> int:
        return sum(p.word_count for p in self.pages)


def extract_metadata(pdf_path: str) -> dict:
    """Extract PDF metadata using pypdf."""
    try:
        reader = PdfReader(pdf_path)
        meta = reader.metadata or {}
        return {
            "title": meta.get("/Title", ""),
            "author": meta.get("/Author", ""),
            "creator": meta.get("/Creator", ""),
            "creation_date": str(meta.get("/CreationDate", "")),
            "page_count": len(reader.pages),
        }
    except Exception as e:
        logger.warning(f"Metadata extraction failed: {e}")
        return {}


def clean_text(raw: str) -> str:
    """Normalize extracted text — remove noise, fix spacing."""
    if not raw:
        return ""
    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", raw)
    # Remove page numbers (standalone digits on a line)
    text = re.sub(r"(?m)^\s*\d{1,4}\s*$", "", text)
    # Remove footer/header boilerplate patterns
    text = re.sub(r"(?i)(confidential|proprietary|all rights reserved)[^\n]*", "", text)
    # Fix common PDF extraction artifacts
    text = text.replace("\x00", "").replace("\ufffd", "")
    # Normalize dashes
    text = re.sub(r"[–—]", "-", text)
    return text.strip()


def detect_section(text: str) -> str:
    """Guess the section type from the first 200 chars of a page."""
    header_area = text[:200].lower()
    if any(k in header_area for k in ["environmental", "climate", "carbon", "energy", "water", "emissions"]):
        return "environmental"
    if any(k in header_area for k in ["social", "community", "diversity", "employee", "human rights"]):
        return "social"
    if any(k in header_area for k in ["governance", "board", "ethics", "compliance", "audit"]):
        return "governance"
    if any(k in header_area for k in ["esg", "sustainability", "csr", "responsibility"]):
        return "sustainability"
    return "general"


def is_esg_relevant(text: str) -> bool:
    """Quick heuristic: does this page contain meaningful ESG content?"""
    esg_signals = [
        "sustainability", "environmental", "social", "governance", "esg",
        "carbon", "emissions", "diversity", "inclusion", "climate", "energy",
        "water", "waste", "community", "human rights", "compliance", "ethics",
        "renewable", "biodiversity", "safety", "wellbeing",
    ]
    lower = text.lower()
    hits = sum(1 for s in esg_signals if s in lower)
    return hits >= 3  # at least 3 ESG signals


def parse_pdf(pdf_path: str, max_pages: Optional[int] = None) -> ParsedReport:
    """
    Main entry point. Parse a PDF and return a ParsedReport object.

    Args:
        pdf_path: Path to the PDF file.
        max_pages: Optional cap on pages to process (useful for huge docs).

    Returns:
        ParsedReport with extracted pages and metadata.
    """
    report = ParsedReport(pdf_path)
    report.metadata = extract_metadata(pdf_path)

    try:
        with pdfplumber.open(pdf_path) as pdf:
            report.total_pages = len(pdf.pages)
            pages_to_process = pdf.pages[:max_pages] if max_pages else pdf.pages

            for i, page in enumerate(pages_to_process):
                try:
                    # pdfplumber gives better layout-aware extraction
                    raw_text = page.extract_text(x_tolerance=3, y_tolerance=3) or ""
                    text = clean_text(raw_text)

                    if len(text) < 30:  # Skip near-empty pages
                        continue

                    section = detect_section(text)
                    rp = ReportPage(page_num=i + 1, text=text, section_hint=section)
                    report.pages.append(rp)

                    if is_esg_relevant(text):
                        report.esg_page_indices.append(len(report.pages) - 1)

                except Exception as e:
                    logger.warning(f"Page {i+1} extraction failed: {e}")
                    continue

    except Exception as e:
        logger.error(f"PDF parsing failed for {pdf_path}: {e}")
        raise RuntimeError(f"Could not parse PDF: {e}") from e

    logger.info(
        f"Parsed '{report.filename}': {len(report.pages)} pages extracted, "
        f"{len(report.esg_page_indices)} ESG-relevant pages, "
        f"{report.word_count:,} total words"
    )
    return report


def extract_tables_text(pdf_path: str) -> str:
    """Extract text from tables in the PDF (useful for metric disclosures)."""
    table_texts = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        row_text = " | ".join(str(cell or "").strip() for cell in row)
                        if row_text.strip():
                            table_texts.append(row_text)
    except Exception as e:
        logger.warning(f"Table extraction failed: {e}")
    return "\n".join(table_texts)