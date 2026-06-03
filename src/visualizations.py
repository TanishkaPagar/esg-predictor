"""
ESG Visualization: Plotly-based charts for Streamlit dashboard.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from src.esg_taxonomy import SCORE_BANDS

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
COLORS = {
    "environmental": "#2ecc71",
    "social": "#3498db",
    "governance": "#9b59b6",
    "background": "#0f1117",
    "surface": "#1a1d27",
    "text": "#e8eaed",
    "muted": "#8892a4",
    "accent": "#f39c12",
}


def make_radar_chart(e_score: float, s_score: float, g_score: float, company_name: str) -> go.Figure:
    """ESG pillar radar/spider chart."""
    categories = ["Environmental", "Social", "Governance"]
    values = [e_score, s_score, g_score]
    values_closed = values + [values[0]]
    categories_closed = categories + [categories[0]]

    fig = go.Figure()

    # Industry average reference (typical mid-tier)
    avg_values = [52, 55, 50]
    avg_closed = avg_values + [avg_values[0]]
    fig.add_trace(go.Scatterpolar(
        r=avg_closed,
        theta=categories_closed,
        fill="toself",
        name="Industry Avg",
        line=dict(color="#555", dash="dash"),
        fillcolor="rgba(85,85,85,0.15)",
    ))

    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill="toself",
        name=company_name,
        line=dict(color="#3498db", width=2.5),
        fillcolor="rgba(52,152,219,0.2)",
        marker=dict(size=8, color="#3498db"),
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True, range=[0, 100],
                tickfont=dict(color=COLORS["muted"], size=10),
                gridcolor="#2d3748",
                linecolor="#2d3748",
            ),
            angularaxis=dict(
                tickfont=dict(color=COLORS["text"], size=12),
                linecolor="#2d3748",
                gridcolor="#2d3748",
            ),
            bgcolor=COLORS["surface"],
        ),
        paper_bgcolor=COLORS["background"],
        plot_bgcolor=COLORS["background"],
        font=dict(color=COLORS["text"]),
        legend=dict(
            font=dict(color=COLORS["text"]),
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=60, r=60, t=40, b=40),
        height=380,
    )
    return fig


def make_score_gauge(score: float, rating: str, color: str) -> go.Figure:
    """Circular gauge showing composite ESG score."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        number={"suffix": "/100", "font": {"size": 36, "color": COLORS["text"]}},
        delta={"reference": 55, "suffix": " vs avg", "font": {"size": 14}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": COLORS["muted"], "tickwidth": 1},
            "bar": {"color": color, "thickness": 0.3},
            "bgcolor": COLORS["surface"],
            "borderwidth": 0,
            "steps": [
                {"range": [0, 25], "color": "#922b21"},
                {"range": [25, 40], "color": "#c0392b"},
                {"range": [40, 55], "color": "#e67e22"},
                {"range": [55, 70], "color": "#f39c12"},
                {"range": [70, 85], "color": "#27ae60"},
                {"range": [85, 100], "color": "#2ecc71"},
            ],
            "threshold": {
                "line": {"color": "white", "width": 3},
                "thickness": 0.8,
                "value": score,
            },
        },
        title={"text": f"<b>{rating}</b>", "font": {"size": 20, "color": COLORS["text"]}},
    ))

    fig.update_layout(
        paper_bgcolor=COLORS["background"],
        font=dict(color=COLORS["text"]),
        margin=dict(l=20, r=20, t=30, b=20),
        height=280,
    )
    return fig


def make_pillar_bar_chart(e_score: float, s_score: float, g_score: float) -> go.Figure:
    """Horizontal bar chart for pillar scores."""
    pillars = ["Environmental", "Social", "Governance"]
    scores = [e_score, s_score, g_score]
    colors = [COLORS["environmental"], COLORS["social"], COLORS["governance"]]

    fig = go.Figure()

    # Background bars (max 100)
    fig.add_trace(go.Bar(
        y=pillars, x=[100, 100, 100],
        orientation="h",
        marker_color="#1e2535",
        showlegend=False,
        hoverinfo="skip",
    ))

    # Score bars
    fig.add_trace(go.Bar(
        y=pillars, x=scores,
        orientation="h",
        marker_color=colors,
        text=[f"{s:.0f}" for s in scores],
        textposition="inside",
        textfont=dict(color="white", size=14, family="monospace"),
        showlegend=False,
        hovertemplate="%{y}: %{x:.1f}/100<extra></extra>",
    ))

    # Industry average reference line
    fig.add_vline(x=55, line_dash="dash", line_color="#555", annotation_text="Avg",
                  annotation_font_color="#555")

    fig.update_layout(
        barmode="overlay",
        paper_bgcolor=COLORS["background"],
        plot_bgcolor=COLORS["background"],
        font=dict(color=COLORS["text"]),
        xaxis=dict(range=[0, 105], gridcolor="#1e2535", tickcolor=COLORS["muted"]),
        yaxis=dict(gridcolor="#1e2535"),
        margin=dict(l=10, r=10, t=20, b=20),
        height=200,
    )
    return fig


def make_keyword_heatmap(top_keywords: list[tuple]) -> go.Figure:
    """Treemap of top ESG keywords by weighted score."""
    if not top_keywords:
        return go.Figure()

    labels = [k[0] for k in top_keywords[:20]]
    values = [max(k[1], 0.1) for k in top_keywords[:20]]

    # Assign pillar colors based on keyword membership
    from src.esg_taxonomy import ENVIRONMENTAL_KEYWORDS, SOCIAL_KEYWORDS, GOVERNANCE_KEYWORDS
    color_map = []
    for label in labels:
        if label in ENVIRONMENTAL_KEYWORDS:
            color_map.append(COLORS["environmental"])
        elif label in SOCIAL_KEYWORDS:
            color_map.append(COLORS["social"])
        else:
            color_map.append(COLORS["governance"])

    fig = go.Figure(go.Treemap(
        labels=labels,
        values=values,
        parents=[""] * len(labels),
        marker=dict(colors=color_map, line=dict(width=1, color=COLORS["background"])),
        textfont=dict(color="white", size=12),
        hovertemplate="<b>%{label}</b><br>Signal Strength: %{value:.2f}<extra></extra>",
    ))

    fig.update_layout(
        paper_bgcolor=COLORS["background"],
        margin=dict(l=0, r=0, t=0, b=0),
        height=250,
    )
    return fig


def make_comparison_bar(companies: list[str], scores: list[float],
                        e_scores: list[float], s_scores: list[float], g_scores: list[float]) -> go.Figure:
    """Grouped bar chart comparing multiple companies."""
    fig = go.Figure()

    fig.add_trace(go.Bar(name="Environmental", x=companies, y=e_scores,
                         marker_color=COLORS["environmental"], opacity=0.85))
    fig.add_trace(go.Bar(name="Social", x=companies, y=s_scores,
                         marker_color=COLORS["social"], opacity=0.85))
    fig.add_trace(go.Bar(name="Governance", x=companies, y=g_scores,
                         marker_color=COLORS["governance"], opacity=0.85))

    # Composite score line
    fig.add_trace(go.Scatter(
        x=companies, y=scores, mode="markers+lines",
        name="Composite", marker=dict(size=12, color="#f39c12"),
        line=dict(color="#f39c12", width=2, dash="dot"),
    ))

    fig.update_layout(
        barmode="group",
        paper_bgcolor=COLORS["background"],
        plot_bgcolor=COLORS["background"],
        font=dict(color=COLORS["text"]),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=COLORS["text"])),
        xaxis=dict(gridcolor="#1e2535"),
        yaxis=dict(range=[0, 105], gridcolor="#1e2535", title="Score (0–100)"),
        margin=dict(l=10, r=10, t=20, b=40),
        height=380,
    )
    return fig


def score_to_color(score: float) -> str:
    """Return hex color for a score value."""
    for lo, hi, _, _, color in SCORE_BANDS:
        if lo <= score <= hi:
            return color
    return "#95a5a6"