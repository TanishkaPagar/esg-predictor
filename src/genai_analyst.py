"""
GenAI ESG Analyst: Uses Claude API to generate deep qualitative insights
from extracted ESG text — beyond what keyword scoring alone can surface.
"""

import re
import json
import logging
import anthropic

logger = logging.getLogger(__name__)

import os
try:
    import streamlit as st
    api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
except:
    api_key = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=api_key)

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a senior ESG analyst at a top-tier asset management firm, 
specializing in sustainable finance and corporate ESG assessment. You analyze corporate 
reports to identify ESG signals, risks, and opportunities.

Your analysis must be:
- Grounded in the provided text excerpts
- Structured following GRI, SASB, and TCFD frameworks
- Objective and evidence-based
- Actionable for institutional investors

Always respond in valid JSON format as specified."""


def _build_analysis_prompt(text_excerpt: str, company_name: str) -> str:
    return f"""Analyze the following excerpt from {company_name}'s corporate report for ESG signals.

TEXT EXCERPT:
{text_excerpt[:4000]}

Provide your analysis as a JSON object with exactly this structure:
{{
  "esg_summary": "2-3 sentence overall ESG assessment",
  "environmental": {{
    "strengths": ["list of 2-4 specific environmental strengths found in the text"],
    "risks": ["list of 1-3 environmental risks or gaps"],
    "notable_commitments": ["specific quantitative targets or pledges mentioned"]
  }},
  "social": {{
    "strengths": ["list of 2-4 specific social strengths found in the text"],
    "risks": ["list of 1-3 social risks or gaps"],
    "notable_commitments": ["specific quantitative targets or pledges mentioned"]
  }},
  "governance": {{
    "strengths": ["list of 2-4 specific governance strengths found in the text"],
    "risks": ["list of 1-3 governance risks or gaps"],
    "notable_commitments": ["specific policies or frameworks mentioned"]
  }},
  "red_flags": ["any significant ESG red flags or controversies detected"],
  "competitive_positioning": "brief assessment of ESG maturity vs typical peer companies",
  "investor_relevance": "why these ESG factors matter to institutional investors",
  "confidence": "high/medium/low - how confident are you based on information available"
}}

Return ONLY the JSON object, no other text."""


def _build_comparison_prompt(results: list[dict]) -> str:
    summaries = "\n".join([
        f"Company: {r['company']}, Score: {r['score']}/100, "
        f"E:{r['e_score']} S:{r['s_score']} G:{r['g_score']}"
        for r in results
    ])
    return f"""Compare the following companies' ESG profiles:

{summaries}

Return a JSON object:
{{
  "ranking": ["ordered list of companies from best to worst ESG"],
  "leader": "company with best overall ESG",
  "key_differentiators": ["main factors separating top from bottom performers"],
  "sector_observations": "observations about ESG maturity in this set",
  "investment_implication": "brief note for ESG-focused investors"
}}

Return ONLY the JSON object."""


# ---------------------------------------------------------------------------
# Main analysis functions
# ---------------------------------------------------------------------------

def analyze_with_ai(text_excerpt: str, company_name: str) -> dict:
    """
    Run GenAI analysis on report text.
    Returns structured insights dict.
    """
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": _build_analysis_prompt(text_excerpt, company_name)}
            ]
        )

        raw = response.content[0].text.strip()

        # Strip markdown code fences if present
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        return json.loads(raw)

    except json.JSONDecodeError as e:
        logger.error(f"AI response JSON parse error: {e}")
        return {"error": "Failed to parse AI response", "raw": raw[:500]}
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        return {"error": str(e)}


def compare_companies_with_ai(results: list[dict]) -> dict:
    """
    Run GenAI comparison across multiple scored companies.
    """
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": _build_comparison_prompt(results)}
            ]
        )

        raw = response.content[0].text.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        return json.loads(raw)

    except Exception as e:
        logger.error(f"Comparison AI analysis failed: {e}")
        return {"error": str(e)}


def generate_executive_summary(score_result, ai_insights: dict) -> str:
    """
    Generate a polished executive summary combining quantitative scores
    and qualitative AI insights.
    """
    try:
        prompt = f"""Based on this ESG analysis, write a concise 3-paragraph executive summary 
suitable for an ESG research note:

Company: {score_result.company_name}
Overall ESG Score: {score_result.total_score}/100 ({score_result.rating} - {score_result.rating_label})
Environmental Score: {score_result.environmental.normalized_score}/100
Social Score: {score_result.social.normalized_score}/100
Governance Score: {score_result.governance.normalized_score}/100

AI Insights: {json.dumps(ai_insights, indent=2)[:1500]}

Write in a professional, investor-facing tone. No headers, just 3 flowing paragraphs.
Keep it under 250 words."""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()

    except Exception as e:
        logger.error(f"Executive summary generation failed: {e}")
        return "Executive summary generation failed. Please check your API connection."