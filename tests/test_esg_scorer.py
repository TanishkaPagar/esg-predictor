"""
Unit tests for the ESG scoring engine.
Run with: python -m pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import MagicMock, patch
from src.esg_scorer import score_pillar, ESGScorer, split_sentences, extract_keyword_hits
from src.esg_taxonomy import ENVIRONMENTAL_KEYWORDS, SOCIAL_KEYWORDS, GOVERNANCE_KEYWORDS, get_score_band


# ---------------------------------------------------------------------------
# Taxonomy tests
# ---------------------------------------------------------------------------

def test_score_bands_full_coverage():
    """Every score 0–100 should map to a valid band."""
    for score in range(0, 101):
        band = get_score_band(score)
        assert band["rating"] != "N/A", f"Score {score} has no valid band"
        assert band["color"].startswith("#")


def test_keywords_have_valid_weights():
    """All keyword weights should be non-zero floats."""
    for kw_dict in [ENVIRONMENTAL_KEYWORDS, SOCIAL_KEYWORDS, GOVERNANCE_KEYWORDS]:
        for kw, weight in kw_dict.items():
            assert isinstance(weight, (int, float)), f"{kw} has non-numeric weight"
            assert weight != 0, f"{kw} has zero weight"


# ---------------------------------------------------------------------------
# Text processing tests
# ---------------------------------------------------------------------------

def test_split_sentences_basic():
    text = "We reduced emissions by 30%. Our renewable energy target is 100% by 2030. Great progress."
    sents = split_sentences(text)
    assert len(sents) >= 2


def test_extract_keyword_hits_positive():
    text = "The company achieved carbon neutral status and invested in renewable energy."
    hits = extract_keyword_hits(text, ENVIRONMENTAL_KEYWORDS)
    assert "carbon neutral" in hits
    assert "renewable energy" in hits
    assert hits["carbon neutral"] > 0


def test_extract_keyword_hits_negative():
    text = "Allegations of child labor in the supply chain were investigated."
    hits = extract_keyword_hits(text, SOCIAL_KEYWORDS)
    assert "child labor" in hits
    assert hits["child labor"] < 0  # Negative signal


def test_extract_keyword_hits_empty_text():
    hits = extract_keyword_hits("", ENVIRONMENTAL_KEYWORDS)
    assert hits == {}


# ---------------------------------------------------------------------------
# Pillar scoring tests
# ---------------------------------------------------------------------------

def test_score_pillar_strong_text():
    """A text with many ESG signals should score well above 50."""
    strong_text = """
    Our company achieved carbon neutral status in 2023. We have committed to net zero emissions by 2040,
    aligned with science based targets (SBTi). 100% renewable energy sourced for all operations.
    Water recycling rate improved by 45%. Zero waste to landfill achieved. Scope 1, 2, and 3 emissions
    all reduced. We invested $200 million in biodiversity projects and reforestation.
    """
    ps = score_pillar(strong_text, ENVIRONMENTAL_KEYWORDS, "Environmental", len(strong_text.split()))
    assert ps.normalized_score > 55, f"Expected >55, got {ps.normalized_score}"


def test_score_pillar_weak_text():
    """A text with no ESG signals should score low."""
    weak_text = "Revenue increased by 15%. Our new product line launched in Q3. Market share grew."
    ps = score_pillar(weak_text, ENVIRONMENTAL_KEYWORDS, "Environmental", len(weak_text.split()))
    assert ps.normalized_score < 40, f"Expected <40, got {ps.normalized_score}"


def test_score_pillar_negative_signals():
    """Negative keywords should drag the score down."""
    text = "The company faces allegations of fraud and corruption in multiple subsidiaries."
    ps = score_pillar(text, GOVERNANCE_KEYWORDS, "Governance", len(text.split()))
    assert ps.normalized_score < 50


def test_score_pillar_returns_confidence():
    text = "We invested in renewable energy and reduced carbon footprint significantly."
    ps = score_pillar(text, ENVIRONMENTAL_KEYWORDS, "Environmental", 100)
    assert 0.0 <= ps.confidence <= 1.0


def test_score_pillar_short_text_returns_zero():
    """Very short text should return zero score (insufficient evidence)."""
    ps = score_pillar("Short.", ENVIRONMENTAL_KEYWORDS, "Environmental", 5)
    assert ps.normalized_score == 0.0


# ---------------------------------------------------------------------------
# ESGScorer integration tests
# ---------------------------------------------------------------------------

def _make_mock_report(text: str, esg_pages: int = 2):
    """Create a minimal mock ParsedReport."""
    report = MagicMock()
    report.full_text = text
    report.esg_focused_text = text
    report.esg_page_indices = list(range(esg_pages))
    report.total_pages = 20
    report.word_count = len(text.split())
    report.filename = "test_report.pdf"
    return report


def test_esg_scorer_returns_result():
    scorer = ESGScorer()
    report = _make_mock_report(
        "We committed to net zero by 2040. Renewable energy at 80%. "
        "Diversity and inclusion programs for all employees. Board independence at 70%."
        "Anti-corruption policies in place with whistleblower hotline."
    )
    result = scorer.score(report, "TestCorp")
    assert result.company_name == "TestCorp"
    assert 0 <= result.total_score <= 100
    assert result.rating != ""
    assert result.environmental is not None
    assert result.social is not None
    assert result.governance is not None


def test_esg_scorer_composite_within_bounds():
    scorer = ESGScorer()
    report = _make_mock_report("carbon neutral net zero renewable energy diversity inclusion governance ethics")
    result = scorer.score(report, "BoundsTest")
    assert 0 <= result.total_score <= 100


def test_esg_scorer_pillar_weights_sum():
    from src.esg_taxonomy import PILLAR_WEIGHTS
    total = sum(PILLAR_WEIGHTS.values())
    assert abs(total - 1.0) < 0.001, f"Pillar weights should sum to 1.0, got {total}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])