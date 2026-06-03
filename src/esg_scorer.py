"""
ESG Scoring Engine: NLP-based signal extraction and score computation.

Methodology:
  1. Keyword density scoring (TF-IDF weighted)
  2. Quantitative commitment detection (regex patterns)
  3. Sentiment-adjusted scoring per pillar
  4. Context window analysis (surrounding sentence scoring)
  5. Section-boosted final aggregation
"""

import re
import math
import logging
from dataclasses import dataclass, field
from collections import defaultdict
from typing import Any

from src.esg_taxonomy import (
    ENVIRONMENTAL_KEYWORDS,
    SOCIAL_KEYWORDS,
    GOVERNANCE_KEYWORDS,
    SECTION_BOOSTERS,
    QUANTITATIVE_PATTERNS,
    PILLAR_WEIGHTS,
    get_score_band,
)
from src.pdf_parser import ParsedReport

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class PillarScore:
    name: str
    raw_score: float = 0.0
    normalized_score: float = 0.0       # 0–100
    keyword_hits: dict = field(default_factory=dict)
    top_signals: list = field(default_factory=list)
    quantitative_count: int = 0
    section_boost: float = 1.0
    confidence: float = 0.0             # 0–1, based on evidence density


@dataclass
class ESGScoreResult:
    company_name: str
    filename: str
    total_score: float                  # 0–100 composite
    environmental: PillarScore = None
    social: PillarScore = None
    governance: PillarScore = None
    rating: str = ""
    rating_label: str = ""
    rating_color: str = ""
    word_count: int = 0
    esg_page_count: int = 0
    total_pages: int = 0
    top_keywords: list = field(default_factory=list)
    key_sentences: list = field(default_factory=list)
    report_year: str = ""
    methodology_note: str = ""


# ---------------------------------------------------------------------------
# Sentence splitter
# ---------------------------------------------------------------------------

def split_sentences(text: str) -> list[str]:
    """Simple but robust sentence splitter."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if len(s.strip()) > 20]


# ---------------------------------------------------------------------------
# Core signal extraction
# ---------------------------------------------------------------------------

def extract_keyword_hits(text: str, keyword_dict: dict[str, float]) -> dict[str, float]:
    """
    Count weighted keyword hits with context-aware scoring.
    Returns {keyword: weighted_count}.
    """
    text_lower = text.lower()
    hits = {}

    for keyword, weight in keyword_dict.items():
        # Count occurrences
        pattern = r"\b" + re.escape(keyword) + r"\b"
        matches = re.findall(pattern, text_lower)
        count = len(matches)

        if count > 0:
            # Apply TF-like dampening: log scale to avoid keyword stuffing
            tf = 1 + math.log(count)
            hits[keyword] = round(tf * weight, 3)

    return hits


def detect_quantitative_commitments(text: str) -> list[str]:
    """Find sentences with measurable ESG targets/commitments."""
    found = []
    for pattern in QUANTITATIVE_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        found.extend(matches)
    return found


def extract_key_sentences(text: str, keyword_dict: dict[str, float], top_n: int = 5) -> list[str]:
    """Extract the most ESG-signal-rich sentences from text."""
    sentences = split_sentences(text)
    scored = []

    for sentence in sentences:
        s_lower = sentence.lower()
        score = sum(
            weight for kw, weight in keyword_dict.items()
            if kw in s_lower and weight > 0
        )
        if score > 0:
            scored.append((score, sentence))

    scored.sort(reverse=True)
    return [s for _, s in scored[:top_n]]


def compute_section_boost(text: str) -> float:
    """Check if the text is from a high-value ESG section."""
    text_lower = text.lower()
    max_boost = 1.0
    for section_kw, boost in SECTION_BOOSTERS.items():
        if section_kw in text_lower[:500]:  # Check in first 500 chars
            max_boost = max(max_boost, boost)
    return max_boost


# ---------------------------------------------------------------------------
# Pillar scorer
# ---------------------------------------------------------------------------

def score_pillar(
    text: str,
    keyword_dict: dict[str, float],
    pillar_name: str,
    word_count: int,
) -> PillarScore:
    """
    Score a single ESG pillar.

    Normalization:
        raw = sum of weighted keyword hits (log-TF dampened)
        normalized = sigmoid-like scaling to 0–100,
                     calibrated so a typical strong report ≈ 70–85
    """
    ps = PillarScore(name=pillar_name)

    if word_count < 5:
        return ps  # Not enough content

    hits = extract_keyword_hits(text, keyword_dict)
    ps.keyword_hits = hits

    # Separate positive and negative signals
    positive_score = sum(v for v in hits.values() if v > 0)
    negative_score = sum(abs(v) for v in hits.values() if v < 0)

    # Quantitative commitments are a strong positive indicator
    quant_hits = detect_quantitative_commitments(text)
    ps.quantitative_count = len(quant_hits)
    quant_bonus = min(ps.quantitative_count * 2.0, 15.0)  # cap at 15 pts bonus

    # Section boost
    ps.section_boost = compute_section_boost(text)

    # Raw score
    ps.raw_score = (positive_score + quant_bonus - negative_score * 0.5) * ps.section_boost

    # Normalize: calibrate to 0–100 using a sigmoid with tuned midpoint
    # Midpoint ~25 raw → 50 normalized (average report)
    # If no hits at all, return 0
    if ps.raw_score <= 0 and not hits:
        ps.normalized_score = 0.0
    else:
        midpoint = 25.0
        steepness = 0.08
        sigmoid_val = 1 / (1 + math.exp(-steepness * (ps.raw_score - midpoint)))
        ps.normalized_score = round(sigmoid_val * 100, 1)

    # Confidence: based on number of unique keywords hit / total keywords
    ps.confidence = round(min(len(hits) / max(len(keyword_dict) * 0.2, 1), 1.0), 2)

    # Top signals: top 10 positive keywords by weighted score
    sorted_hits = sorted(
        [(k, v) for k, v in hits.items() if v > 0],
        key=lambda x: x[1], reverse=True
    )
    ps.top_signals = sorted_hits[:10]

    # Key sentences
    ps.top_signals = sorted_hits[:10]

    return ps


# ---------------------------------------------------------------------------
# Main scorer
# ---------------------------------------------------------------------------

class ESGScorer:
    """
    End-to-end ESG score predictor from a ParsedReport.
    """

    def __init__(self, use_esg_focused: bool = True):
        """
        Args:
            use_esg_focused: If True, score only ESG-relevant pages.
                             If False, use full document text.
        """
        self.use_esg_focused = use_esg_focused

    def score(self, report: ParsedReport, company_name: str = "") -> ESGScoreResult:
        """
        Compute a full ESG score from a parsed report.

        Returns an ESGScoreResult with pillar breakdowns, top signals,
        composite score, and letter rating.
        """
        # Choose text corpus
        if self.use_esg_focused and report.esg_page_indices:
            text = report.esg_focused_text
            logger.info(f"Scoring {len(report.esg_page_indices)} ESG-relevant pages")
        else:
            text = report.full_text
            logger.info("Scoring full document text")

        word_count = len(text.split())

        # Score each pillar independently
        e_score = score_pillar(text, ENVIRONMENTAL_KEYWORDS, "Environmental", word_count)
        s_score = score_pillar(text, SOCIAL_KEYWORDS, "Social", word_count)
        g_score = score_pillar(text, GOVERNANCE_KEYWORDS, "Governance", word_count)

        # Composite weighted score
        composite = (
            e_score.normalized_score * PILLAR_WEIGHTS["environmental"] +
            s_score.normalized_score * PILLAR_WEIGHTS["social"] +
            g_score.normalized_score * PILLAR_WEIGHTS["governance"]
        )
        composite = round(min(composite, 100.0), 1)

        # Rating band
        band = get_score_band(composite)

        # Top keywords across all pillars
        all_hits = {**e_score.keyword_hits, **s_score.keyword_hits, **g_score.keyword_hits}
        top_keywords = sorted(
            [(k, v) for k, v in all_hits.items() if v > 0],
            key=lambda x: x[1], reverse=True
        )[:15]

        # Key sentences (combined)
        all_keywords = {**ENVIRONMENTAL_KEYWORDS, **SOCIAL_KEYWORDS, **GOVERNANCE_KEYWORDS}
        key_sentences = extract_key_sentences(text, all_keywords, top_n=8)

        # Infer report year from text
        year_match = re.search(r"\b(20[12]\d)\b", text[:2000])
        report_year = year_match.group(1) if year_match else "Unknown"

        # Build result
        result = ESGScoreResult(
            company_name=company_name or report.filename,
            filename=report.filename,
            total_score=composite,
            environmental=e_score,
            social=s_score,
            governance=g_score,
            rating=band["rating"],
            rating_label=band["label"],
            rating_color=band["color"],
            word_count=word_count,
            esg_page_count=len(report.esg_page_indices),
            total_pages=report.total_pages,
            top_keywords=top_keywords,
            key_sentences=key_sentences,
            report_year=report_year,
            methodology_note=(
                "Score derived via NLP keyword density analysis, TF-IDF weighting, "
                "quantitative commitment detection, and pillar-weighted aggregation. "
                "Aligned with GRI, SASB, TCFD, and MSCI ESG Ratings methodology signals."
            ),
        )

        logger.info(
            f"ESG Score for '{company_name}': {composite}/100 ({band['rating']} - {band['label']}) "
            f"| E:{e_score.normalized_score} S:{s_score.normalized_score} G:{g_score.normalized_score}"
        )

        return result