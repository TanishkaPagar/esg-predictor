# 🌱 ESG Score Predictor from Company Reports

An AI-powered tool that automatically analyzes company annual reports and sustainability documents to predict ESG (Environmental, Social, and Governance) scores using NLP and Generative AI.

## 🔗 Live Demo
[https://esg-predictor.streamlit.app/](https://esg-predictor.streamlit.app/)

## 🛠️ Tech Stack
- Python 3.13
- NLP (Natural Language Processing)
- Generative AI
- PDF Parsing
- Streamlit

## ✨ Features
- Upload any company annual report or sustainability report in PDF format
- Automatically extracts ESG signals using keyword analysis and NLP
- Predicts ESG score across three pillars — Environmental, Social and Governance
- Generates AI-powered qualitative insights and investor-facing summary
- Interactive visual dashboard of results

## ⚙️ How to Run Locally

### Prerequisites
- Python 3.13
- pip

### Steps

1. Clone the repository
git clone https://github.com/TanishkaPagar/esg-predictor.git
cd esg-predictor

2. Install dependencies
pip install -r requirements.txt

3. Add your API key
Create a .env file and add:
GOOGLE_API_KEY=your_api_key_here

4. Run the app
streamlit run app.py

5. Open in browser
http://localhost:8501

## 📂 Project Structure
esg-predictor/
├── app.py                  # Main Streamlit app
├── requirements.txt        # Dependencies
├── README.md               # Project documentation
└── .env                    # API key (not uploaded to GitHub)

## 🔬 Research Focus
Automated ESG Intelligence from Unstructured Corporate Disclosures

## 👩‍💻 Developed By
Tanishka Pagar — LABTECH Internship 2026