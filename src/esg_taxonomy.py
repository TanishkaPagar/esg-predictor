"""
ESG Taxonomy: Keyword signals, weights, and pillar definitions.
Based on GRI Standards, SASB, TCFD, and MSCI ESG Ratings methodology.
"""

# ---------------------------------------------------------------------------
# ENVIRONMENTAL SIGNALS (E pillar)
# ---------------------------------------------------------------------------
ENVIRONMENTAL_KEYWORDS = {
    # Climate & Emissions
    "carbon neutral": 3.0,
    "net zero": 3.0,
    "carbon footprint": 2.5,
    "greenhouse gas": 2.5,
    "ghg emissions": 2.5,
    "scope 1": 2.0,
    "scope 2": 2.0,
    "scope 3": 2.0,
    "carbon offset": 2.0,
    "emissions reduction": 2.5,
    "climate change": 2.0,
    "climate risk": 2.0,
    "paris agreement": 2.5,
    "science based targets": 3.0,
    "sbti": 3.0,
    "decarbonization": 2.5,
    "low carbon": 2.0,

    # Energy
    "renewable energy": 2.5,
    "solar energy": 2.0,
    "wind energy": 2.0,
    "energy efficiency": 2.5,
    "energy consumption": 1.5,
    "clean energy": 2.0,
    "fossil fuel": -1.0,  # negative signal

    # Water
    "water stewardship": 2.5,
    "water consumption": 1.5,
    "water recycling": 2.0,
    "water risk": 1.5,
    "freshwater": 1.5,

    # Waste & Circular Economy
    "zero waste": 2.5,
    "waste reduction": 2.0,
    "recycling": 1.5,
    "circular economy": 2.5,
    "landfill": -1.0,
    "hazardous waste": -1.5,

    # Biodiversity & Land
    "biodiversity": 2.0,
    "deforestation": -2.0,
    "reforestation": 2.0,
    "land use": 1.0,
    "ecosystem": 1.5,

    # Supply Chain Environment
    "sustainable sourcing": 2.0,
    "sustainable supply chain": 2.0,
    "environmental impact": 1.5,
    "life cycle assessment": 2.0,
    "lca": 1.5,
}

# ---------------------------------------------------------------------------
# SOCIAL SIGNALS (S pillar)
# ---------------------------------------------------------------------------
SOCIAL_KEYWORDS = {
    # Labor & Human Rights
    "human rights": 2.5,
    "labor rights": 2.5,
    "fair wages": 2.0,
    "living wage": 2.5,
    "forced labor": -3.0,
    "child labor": -3.0,
    "modern slavery": -2.5,
    "worker safety": 2.0,
    "occupational health": 2.0,

    # Diversity & Inclusion
    "diversity and inclusion": 2.5,
    "dei": 2.0,
    "gender equality": 2.5,
    "pay equity": 2.5,
    "equal opportunity": 2.0,
    "women in leadership": 2.0,
    "inclusive workplace": 2.0,
    "discrimination": -2.0,

    # Employee Wellbeing
    "employee wellbeing": 2.5,
    "mental health": 2.0,
    "employee engagement": 2.0,
    "talent development": 2.0,
    "training and development": 2.0,
    "employee satisfaction": 2.0,
    "turnover rate": 1.0,
    "workforce development": 2.0,
    "reskilling": 2.0,

    # Community & Society
    "community investment": 2.0,
    "social impact": 2.0,
    "philanthropy": 1.5,
    "corporate social responsibility": 1.5,
    "csr": 1.5,
    "local communities": 1.5,
    "social license": 2.0,

    # Product & Customer
    "product safety": 2.0,
    "data privacy": 2.0,
    "data security": 2.0,
    "customer satisfaction": 1.5,
    "responsible marketing": 2.0,
    "access to healthcare": 2.0,
    "affordable products": 1.5,

    # Supply Chain Social
    "supplier code of conduct": 2.0,
    "supply chain audit": 2.0,
    "responsible sourcing": 2.0,
}

# ---------------------------------------------------------------------------
# GOVERNANCE SIGNALS (G pillar)
# ---------------------------------------------------------------------------
GOVERNANCE_KEYWORDS = {
    # Board & Leadership
    "board independence": 2.5,
    "independent directors": 2.0,
    "board diversity": 2.5,
    "executive compensation": 1.5,
    "say on pay": 2.0,
    "clawback": 2.0,
    "board oversight": 2.0,
    "audit committee": 2.0,
    "risk committee": 1.5,

    # Ethics & Compliance
    "anti-corruption": 2.5,
    "anti-bribery": 2.5,
    "code of ethics": 2.0,
    "code of conduct": 2.0,
    "whistleblower": 2.5,
    "compliance program": 2.0,
    "zero tolerance": 2.0,
    "sanctions": -2.0,
    "fine": -1.5,
    "penalty": -1.5,
    "fraud": -3.0,
    "corruption": -3.0,

    # Transparency & Reporting
    "esg reporting": 3.0,
    "sustainability report": 3.0,
    "gri": 2.5,
    "sasb": 2.5,
    "tcfd": 2.5,
    "integrated reporting": 2.5,
    "third party audit": 2.5,
    "external assurance": 2.5,
    "transparency": 1.5,

    # Risk Management
    "enterprise risk management": 2.0,
    "risk management": 1.5,
    "internal controls": 2.0,
    "cybersecurity": 2.0,
    "data governance": 2.0,

    # Shareholder Rights
    "shareholder rights": 2.0,
    "stakeholder engagement": 2.0,
    "proxy voting": 1.5,
    "dual class shares": -1.5,
    "poison pill": -2.0,
}

# ---------------------------------------------------------------------------
# SECTION BOOSTERS: Weight multipliers for specific document sections
# ---------------------------------------------------------------------------
SECTION_BOOSTERS = {
    "sustainability": 1.5,
    "esg": 1.5,
    "environmental": 1.3,
    "social": 1.3,
    "governance": 1.3,
    "climate": 1.4,
    "responsibility": 1.2,
    "csr report": 1.4,
}

# ---------------------------------------------------------------------------
# QUANTITATIVE INDICATORS: Patterns indicating numeric commitments
# ---------------------------------------------------------------------------
QUANTITATIVE_PATTERNS = [
    r"\b\d+\s*%\s*(reduction|decrease|improvement|increase)\b",
    r"\b(by\s+20\d{2}|by\s+\d{4})\b.*?(target|goal|commitment|aim)",
    r"\b\d+\s*(million|billion|thousand)\s*(trees|tonnes|mwh|mw|kwh)\b",
    r"\bzero\s+(emission|waste|accident|incident)\b",
    r"\b100\s*%\s*(renewable|recycled|sustainable|clean)\b",
]

# ---------------------------------------------------------------------------
# PILLAR WEIGHTS for composite ESG score
# ---------------------------------------------------------------------------
PILLAR_WEIGHTS = {
    "environmental": 0.35,
    "social": 0.35,
    "governance": 0.30,
}

# ---------------------------------------------------------------------------
# SCORE BANDS → Letter ratings
# ---------------------------------------------------------------------------
SCORE_BANDS = [
    (85, 100, "AAA", "Leader", "#2ecc71"),
    (70, 85, "AA",  "Strong", "#27ae60"),
    (55, 70, "A",   "Above Average", "#f39c12"),
    (40, 55, "BBB", "Average", "#e67e22"),
    (25, 40, "BB",  "Below Average", "#e74c3c"),
    (10, 25, "B",   "Weak", "#c0392b"),
    (0,  10, "CCC", "Laggard", "#922b21"),
]

def get_score_band(score: float) -> dict:
    for lo, hi, rating, label, color in SCORE_BANDS:
        if lo <= score <= hi:
            return {"rating": rating, "label": label, "color": color}
    return {"rating": "N/A", "label": "Unknown", "color": "#95a5a6"}