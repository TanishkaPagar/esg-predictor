# 🌱 ESG Score Predictor from Company Reports

An AI-powered tool that automatically analyzes company annual reports and sustainability documents to predict ESG (Environmental, Social, and Governance) scores using NLP and Generative AI (Claude by Anthropic).

## 🔗 Live Demo
[https://esg-predictor.streamlit.app/](https://esg-predictor.streamlit.app/)

## 🛠️ Tech Stack
- Python 3.13
- NLP (Natural Language Processing)
- Generative AI (Claude — Anthropic)
- PDF Parsing (pdfplumber)
- Streamlit

## ✨ Features
- Upload any company annual report or sustainability report in PDF format
- Automatically extracts ESG signals using keyword analysis and NLP
- Predicts ESG score across three pillars — Environmental, Social and Governance
- Generates AI-powered qualitative insights and investor-facing summary
- Compare ESG scores across multiple companies
- Interactive visual dashboard with radar charts, heatmaps and gauges

## ⚙️ How to Run Locally

### Prerequisites
- Python 3.13
- pip
- Anthropic API Key (get it from https://console.anthropic.com/)

### Steps

1. Clone the repository
git clone https://github.com/TanishkaPagar/esg-predictor.git
cd esg-predictor

2. Install dependencies
pip install -r requirements.txt

3. Add your API key
Create a .env file and add:
ANTHROPIC_API_KEY=your_api_key_here

4. Run the app
streamlit run app.py

5. Open in browser
http://localhost:8501

## 📂 Project Structure
esg-predictor/
├── app.py                  # Main Streamlit app
├── requirements.txt        # Dependencies
├── README.md               # Project documentation
├── .env                    # API key (not uploaded to GitHub)
└── src/
    ├── pdf_parser.py       # PDF text extraction
    ├── esg_scorer.py       # ESG scoring logic
    ├── genai_analyst.py    # Claude AI analysis
    └── visualizations.py  # Charts and graphs

## 🔬 Research Focus
Automated ESG Intelligence from Unstructured Corporate Disclosures

## 📊 Scoring Framework
- Keyword density (TF-IDF weighted)
- Quantitative commitment detection
- Section-aware boosting
- GenAI qualitative analysis (Claude)
- Pillar weighting: E(35%) S(35%) G(30%)
- Aligned with: GRI, SASB, TCFD, MSCI ESG

## 👩‍💻 Developed By
Tanishka Pagar — LABTECH Internship 2026