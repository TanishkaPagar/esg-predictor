"""
ESG Score Predictor — Streamlit Application
Automated ESG Intelligence from Unstructured Corporate Disclosures
"""

import os
import sys
import time
import tempfile
import logging
import streamlit as st
import pandas as pd

# Make src importable
sys.path.insert(0, os.path.dirname(__file__))

from src.pdf_parser import parse_pdf
from src.esg_scorer import ESGScorer
from src.genai_analyst import analyze_with_ai, generate_executive_summary, compare_companies_with_ai
from src.visualizations import (
    make_radar_chart, make_score_gauge, make_pillar_bar_chart,
    make_keyword_heatmap, make_comparison_bar, score_to_color,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="ESG Score Predictor",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }

  .main { background-color: #0f1117; }

  .metric-card {
    background: linear-gradient(135deg, #1a1d27 0%, #1e2535 100%);
    border: 1px solid #2d3748;
    border-radius: 12px;
    padding: 20px 24px;
    margin: 6px 0;
  }

  .score-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.1em;
    letter-spacing: 1px;
  }

  .pillar-label {
    font-size: 0.75em;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #8892a4;
    margin-bottom: 4px;
  }

  .signal-tag {
    display: inline-block;
    background: #1e2535;
    border: 1px solid #2d3748;
    border-radius: 6px;
    padding: 3px 10px;
    margin: 3px;
    font-size: 0.82em;
    font-family: 'JetBrains Mono', monospace;
  }

  .key-sentence {
    background: #1a1d27;
    border-left: 3px solid #3498db;
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 0.9em;
    color: #c8d0dc;
    line-height: 1.6;
  }

  .section-header {
    font-size: 0.7em;
    text-transform: uppercase;
    letter-spacing: 3px;
    color: #8892a4;
    border-bottom: 1px solid #2d3748;
    padding-bottom: 8px;
    margin: 20px 0 14px 0;
  }

  .stTabs [data-baseweb="tab-list"] { gap: 8px; }
  .stTabs [data-baseweb="tab"] {
    background: #1a1d27;
    border-radius: 8px 8px 0 0;
    color: #8892a4;
    padding: 8px 20px;
  }
  .stTabs [aria-selected="true"] {
    background: #1e2535 !important;
    color: #e8eaed !important;
  }

  div[data-testid="stMetricValue"] { font-size: 2rem; font-weight: 700; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------
if "results" not in st.session_state:
    st.session_state.results = []
if "ai_insights" not in st.session_state:
    st.session_state.ai_insights = {}


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🌱 ESG Score Predictor")
    st.markdown("*Automated ESG Intelligence from Unstructured Corporate Disclosures*")
    st.divider()

    st.markdown("### ⚙️ Configuration")

    use_ai = st.toggle("Enable GenAI Analysis (Claude)", value=True,
                       help="Uses Claude API for qualitative ESG insights beyond keyword scoring")

    use_esg_focused = st.toggle("Focus on ESG Pages Only", value=True,
                                help="Score only ESG-relevant pages for higher signal-to-noise ratio")

    st.divider()
    st.markdown("### 📋 Methodology")
    st.markdown("""
    **Scoring Framework:**
    - 🔑 Keyword density (TF-IDF weighted)
    - 📊 Quantitative commitment detection
    - 🧭 Section-aware boosting
    - 🤖 GenAI qualitative analysis
    - ⚖️ Pillar weighting: E(35%) S(35%) G(30%)

    **Aligned with:** GRI, SASB, TCFD, MSCI ESG
    """)

    st.divider()
    if st.session_state.results:
        st.markdown(f"**Reports analyzed:** {len(st.session_state.results)}")
        if st.button("🗑 Clear All Results"):
            st.session_state.results = []
            st.session_state.ai_insights = {}
            st.rerun()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("# 🌱 ESG Score Predictor")
    st.markdown("**Predict ESG ratings from annual reports — before agencies publish them**")
with col_h2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<span style="background:#1e2535;padding:6px 14px;border-radius:8px;'
        'font-size:0.75em;color:#8892a4;letter-spacing:2px;">RESEARCH PREVIEW</span>',
        unsafe_allow_html=True
    )

st.divider()

# ---------------------------------------------------------------------------
# Main tabs
# ---------------------------------------------------------------------------
tab_analyze, tab_compare, tab_methodology = st.tabs([
    "📄 Analyze Report", "⚖️ Compare Companies", "🔬 Methodology"
])


# ============================================================
# TAB 1: Single Report Analysis
# ============================================================
with tab_analyze:
    st.markdown("### Upload Corporate Report")
    st.markdown(
        "Upload an annual report, sustainability report, or 10-K PDF to extract ESG signals."
    )

    col_upload, col_meta = st.columns([2, 1])

    with col_upload:
        uploaded_file = st.file_uploader(
            "Drop PDF here", type=["pdf"],
            help="Annual reports, CSR reports, sustainability disclosures, 10-K filings",
        )

    with col_meta:
        company_name = st.text_input("Company Name", placeholder="e.g. Infosys Ltd.")
        max_pages = st.number_input("Max Pages to Parse", min_value=10, max_value=500,
                                    value=150, step=10,
                                    help="Limit parsing for large documents")

    if uploaded_file and company_name:
        if st.button("🔍 Analyze ESG Signals", type="primary", use_container_width=True):

            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            try:
                # Stage 1: Parse PDF
                with st.status("📖 Parsing PDF...", expanded=True) as status:
                    st.write("Extracting text from document...")
                    t0 = time.time()
                    report = parse_pdf(tmp_path, max_pages=int(max_pages))
                    st.write(f"✅ Extracted {len(report.pages)} pages, "
                             f"{report.word_count:,} words, "
                             f"{len(report.esg_page_indices)} ESG-relevant pages")

                    # Stage 2: Score
                    st.write("Computing ESG scores...")
                    scorer = ESGScorer(use_esg_focused=use_esg_focused)
                    result = scorer.score(report, company_name)
                    st.write(f"✅ Composite ESG Score: **{result.total_score}/100** ({result.rating})")

                    # Stage 3: AI Analysis
                    ai_insights = {}
                    exec_summary = ""
                    if use_ai:
                        st.write("🤖 Running GenAI qualitative analysis...")
                        ai_insights = analyze_with_ai(report.esg_focused_text[:5000], company_name)
                        if "error" not in ai_insights:
                            exec_summary = generate_executive_summary(result, ai_insights)
                            st.session_state.ai_insights[company_name] = ai_insights

                    elapsed = time.time() - t0
                    status.update(label=f"✅ Analysis complete in {elapsed:.1f}s", state="complete")

                # Store result
                st.session_state.results.append({
                    "result": result,
                    "exec_summary": exec_summary,
                    "ai_insights": ai_insights,
                })

            except Exception as e:
                st.error(f"❌ Analysis failed: {e}")
                logger.exception("Analysis error")
            finally:
                os.unlink(tmp_path)

    # ── Display latest result ──────────────────────────────────
    if st.session_state.results:
        latest = st.session_state.results[-1]
        result = latest["result"]
        ai_insights = latest["ai_insights"]
        exec_summary = latest["exec_summary"]

        st.divider()

        # ── Score Overview ──
        st.markdown(
            f'<div class="section-header">ESG Assessment — {result.company_name} '
            f'({result.report_year})</div>',
            unsafe_allow_html=True
        )

        col_gauge, col_bars, col_meta2 = st.columns([1.2, 1.5, 1.3])

        with col_gauge:
            st.plotly_chart(
                make_score_gauge(result.total_score, result.rating, result.rating_color),
                use_container_width=True
            )
            st.markdown(
                f'<div style="text-align:center">'
                f'<span class="score-badge" style="background:{result.rating_color}20;'
                f'color:{result.rating_color};border:1px solid {result.rating_color}">'
                f'{result.rating}</span> '
                f'<span style="color:#8892a4;font-size:0.9em">{result.rating_label}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

        with col_bars:
            st.markdown('<div class="pillar-label">Pillar Breakdown</div>', unsafe_allow_html=True)
            st.plotly_chart(make_pillar_bar_chart(
                result.environmental.normalized_score,
                result.social.normalized_score,
                result.governance.normalized_score,
            ), use_container_width=True)

        with col_meta2:
            st.markdown('<div class="pillar-label">Report Stats</div>', unsafe_allow_html=True)
            st.metric("Total Pages", result.total_pages)
            st.metric("ESG Pages", result.esg_page_count)
            st.metric("Word Count", f"{result.word_count:,}")
            confidence_avg = round(
                (result.environmental.confidence + result.social.confidence + result.governance.confidence) / 3, 2
            )
            st.metric("Avg Confidence", f"{confidence_avg:.0%}")

        # ── Radar Chart ──
        st.markdown('<div class="section-header">Pillar Radar vs Industry Average</div>',
                    unsafe_allow_html=True)
        st.plotly_chart(
            make_radar_chart(
                result.environmental.normalized_score,
                result.social.normalized_score,
                result.governance.normalized_score,
                result.company_name,
            ),
            use_container_width=True
        )

        # ── Pillar Detail Tabs ──
        st.markdown('<div class="section-header">Pillar Deep Dive</div>',
                    unsafe_allow_html=True)
        p_env, p_soc, p_gov = st.tabs(["🌿 Environmental", "🤝 Social", "🏛 Governance"])

        def render_pillar_tab(pillar_score, ai_key: str, ai_data: dict):
            col_l, col_r = st.columns([1, 1])
            with col_l:
                st.metric(f"{pillar_score.name} Score",
                          f"{pillar_score.normalized_score:.1f}/100",
                          delta=f"+{pillar_score.quantitative_count} quantitative commitments")

                # Top signals
                st.markdown("**Top Signal Keywords**")
                tags = "".join(
                    f'<span class="signal-tag">{kw} ({score:.1f})</span>'
                    for kw, score in pillar_score.top_signals[:12]
                )
                st.markdown(f'<div>{tags}</div>', unsafe_allow_html=True)

            with col_r:
                if ai_data and "error" not in ai_data and ai_key in ai_data:
                    pillar_ai = ai_data[ai_key]
                    if "strengths" in pillar_ai:
                        st.markdown("**AI-Identified Strengths**")
                        for s in pillar_ai.get("strengths", []):
                            st.markdown(f"✅ {s}")
                    if "risks" in pillar_ai:
                        st.markdown("**Risks / Gaps**")
                        for r in pillar_ai.get("risks", []):
                            st.markdown(f"⚠️ {r}")
                    if pillar_ai.get("notable_commitments"):
                        st.markdown("**Notable Commitments**")
                        for c in pillar_ai["notable_commitments"]:
                            st.markdown(f"🎯 {c}")

        with p_env:
            render_pillar_tab(result.environmental, "environmental", ai_insights)
        with p_soc:
            render_pillar_tab(result.social, "social", ai_insights)
        with p_gov:
            render_pillar_tab(result.governance, "governance", ai_insights)

        # ── Key Sentences ──
        st.markdown('<div class="section-header">High-Signal ESG Sentences</div>',
                    unsafe_allow_html=True)
        for sent in result.key_sentences[:6]:
            st.markdown(f'<div class="key-sentence">{sent}</div>', unsafe_allow_html=True)

        # ── Executive Summary (AI) ──
        if exec_summary:
            st.markdown('<div class="section-header">AI Executive Summary</div>',
                        unsafe_allow_html=True)
            st.markdown(
                f'<div style="background:#1a1d27;border:1px solid #2d3748;border-radius:12px;'
                f'padding:20px;line-height:1.8;color:#c8d0dc">{exec_summary}</div>',
                unsafe_allow_html=True
            )

        # ── Red Flags ──
        if ai_insights and "red_flags" in ai_insights and ai_insights["red_flags"]:
            st.markdown('<div class="section-header">⚠️ Red Flags Detected</div>',
                        unsafe_allow_html=True)
            for flag in ai_insights["red_flags"]:
                st.warning(flag)

        # ── Keyword Heatmap ──
        st.markdown('<div class="section-header">ESG Signal Heatmap (Top 20 Keywords)</div>',
                    unsafe_allow_html=True)
        st.markdown(
            "🟢 Environmental &nbsp;&nbsp; 🔵 Social &nbsp;&nbsp; 🟣 Governance",
            unsafe_allow_html=True
        )
        st.plotly_chart(make_keyword_heatmap(result.top_keywords), use_container_width=True)

        # ── Methodology Note ──
        with st.expander("ℹ️ Methodology Note"):
            st.markdown(result.methodology_note)
            st.markdown(f"""
            **Score Calibration:**
            - Scores are calibrated against GRI-aligned signal density baselines
            - A score of 55–65 represents typical mid-tier corporate disclosures
            - Scores above 75 indicate strong, quantified ESG commitments
            - Negative keywords (e.g., fraud, forced labor) reduce scores

            **Limitations:**
            - Keyword-based scoring may miss narrative context
            - Companies with verbose sustainability sections may score higher
            - This tool supplements but does not replace professional ESG ratings
            """)


# ============================================================
# TAB 2: Company Comparison
# ============================================================
with tab_compare:
    st.markdown("### Compare ESG Scores Across Companies")

    if len(st.session_state.results) < 2:
        st.info("📄 Analyze at least 2 company reports in the **Analyze Report** tab to compare.")
    else:
        results_list = [r["result"] for r in st.session_state.results]

        companies = [r.company_name for r in results_list]
        scores = [r.total_score for r in results_list]
        e_scores = [r.environmental.normalized_score for r in results_list]
        s_scores = [r.social.normalized_score for r in results_list]
        g_scores = [r.governance.normalized_score for r in results_list]

        # ── Summary Table ──
        df = pd.DataFrame({
            "Company": companies,
            "ESG Score": scores,
            "Rating": [r.rating for r in results_list],
            "Environmental": e_scores,
            "Social": s_scores,
            "Governance": g_scores,
            "ESG Pages": [r.esg_page_count for r in results_list],
        })
        df = df.sort_values("ESG Score", ascending=False).reset_index(drop=True)
        df.insert(0, "Rank", range(1, len(df) + 1))

        st.dataframe(
            df.style.background_gradient(subset=["ESG Score", "Environmental", "Social", "Governance"],
                                         cmap="RdYlGn", vmin=0, vmax=100),
            use_container_width=True,
            hide_index=True,
        )

        # ── Comparison Chart ──
        st.plotly_chart(
            make_comparison_bar(companies, scores, e_scores, s_scores, g_scores),
            use_container_width=True
        )

        # ── AI Comparison ──
        if use_ai and st.button("🤖 Generate AI Comparative Analysis"):
            with st.spinner("Analyzing companies..."):
                comparison_data = [
                    {"company": r.company_name, "score": r.total_score,
                     "e_score": r.environmental.normalized_score,
                     "s_score": r.social.normalized_score,
                     "g_score": r.governance.normalized_score}
                    for r in results_list
                ]
                comparison = compare_companies_with_ai(comparison_data)

                if "error" not in comparison:
                    col_c1, col_c2 = st.columns(2)
                    with col_c1:
                        if "leader" in comparison:
                            st.success(f"🏆 ESG Leader: **{comparison['leader']}**")
                        if "ranking" in comparison:
                            st.markdown("**Ranking:**")
                            for i, co in enumerate(comparison["ranking"], 1):
                                st.markdown(f"{i}. {co}")
                    with col_c2:
                        if "key_differentiators" in comparison:
                            st.markdown("**Key Differentiators:**")
                            for d in comparison["key_differentiators"]:
                                st.markdown(f"• {d}")
                        if "investment_implication" in comparison:
                            st.info(f"💼 **Investor Note:** {comparison['investment_implication']}")
                else:
                    st.error(f"AI comparison failed: {comparison['error']}")


# ============================================================
# TAB 3: Methodology
# ============================================================
with tab_methodology:
    st.markdown("### Research Methodology")
    st.markdown("""
    #### Paper Angle: *"Automated ESG Intelligence from Unstructured Corporate Disclosures"*

    This tool implements a multi-layer NLP pipeline to extract ESG signals from unstructured
    PDF reports and predict ESG scores before official rating agencies publish them.
    """)

    col_m1, col_m2 = st.columns(2)

    with col_m1:
        st.markdown("""
        #### 📊 Scoring Pipeline

        **Stage 1 — PDF Parsing**
        - pdfplumber layout-aware extraction
        - Section detection (E/S/G/General)
        - ESG page identification heuristics

        **Stage 2 — Signal Extraction**
        - ~150+ curated ESG keywords per pillar
        - TF-IDF log-dampened frequency weighting
        - Negative signal penalties (e.g., fraud, forced labor)
        - Quantitative commitment detection (regex patterns)

        **Stage 3 — Score Normalization**
        - Sigmoid normalization to 0–100 scale
        - Section-based multipliers (1.0x–1.5x)
        - Pillar weighting: E(35%), S(35%), G(30%)
        - Letter rating bands (AAA → CCC)

        **Stage 4 — GenAI Analysis (Claude)**
        - Qualitative ESG assessment
        - Strengths / risks / red flags
        - Investor-facing executive summary
        """)

    with col_m2:
        st.markdown("""
        #### 📚 Framework Alignment

        | Framework | Coverage |
        |-----------|----------|
        | **GRI Standards** | Environmental disclosures, labor practices |
        | **SASB** | Sector-specific material topics |
        | **TCFD** | Climate risk and governance |
        | **MSCI ESG** | Controversy detection, scoring calibration |
        | **UN SDGs** | Sustainable development goal alignment |

        #### ⚖️ Limitations & Future Work
        - Keyword scoring misses sarcasm and negative context
        - Company verbosity may inflate scores
        - Future: fine-tuned ESG BERT classifier
        - Future: XBRL/structured data integration
        - Future: controversy news feed integration
        - Future: time-series score tracking

        #### 📈 Score Calibration Baseline
        | Band | Score | Typical Profile |
        |------|-------|-----------------|
        | AAA | 85–100 | Net-zero committed, 3rd-party assured |
        | AA | 70–85 | Strong disclosure, quantified targets |
        | A | 55–70 | Above avg, some gaps |
        | BBB | 40–55 | Average corporate disclosure |
        | BB–CCC | 0–40 | Weak/missing ESG disclosure |
        """)

    st.divider()
    st.markdown("""
    #### 🔗 References
    - Global Reporting Initiative (GRI) Standards 2021
    - SASB Standards by Industry (2023)
    - TCFD Recommendations (2017, updated 2022)
    - MSCI ESG Ratings Methodology (2023)
    - Berg, F., Kölbel, J., Rigobon, R. (2022). *Aggregate Confusion: The Divergence of ESG Ratings*. RFS.
    """)