> **"In a crisis, the problem isn't not knowing—it's knowing too much, too late."**

AstraCode is an AI-powered Risk Intelligence Platform designed for Supply Chain Managers and National Security Analysts. It ingests real-time news, quantifies risk velocity, and forecasts national stability trends 4 hours in advance.

---

## 🚀 The Problem
Traditional news monitoring is **reactive**. By the time a "Riots" headline reaches a dashboard, the supply chain is already disrupted.
**AstraCode is proactive.** It calculates the **Velocity** of news (rate of acceleration) to predict crises before they peak.

## ⚡ Key Features

- **🧠 Zero-Shot AI Classification:** Uses `DistilBART-MNLI` to classify news into *Civil Unrest, Economic Crisis, or Natural Disaster* without retraining.
- **📍 Deterministic Geolocation:** Custom NLP engine maps risks to precise GPS coordinates in Sri Lanka (avoiding AI hallucinations).
- **📉 Predictive Forecasting:** Uses **Linear Regression** on risk scores to forecast the trend (Deteriorating/Improving) for the next 4 hours.
- **🔥 Trend Detection:** Unsupervised Machine Learning (**TF-IDF + K-Means**) automatically detects emerging narratives (e.g., "Fuel Strike").
- **📊 Real-Time Dashboard:** Built with **Streamlit** for sub-second data visualization.

---

## 🛠️ Architecture

AstraCode avoids "Black Box" APIs in favor of a locally running, transparent architecture:

| Component | Tech Stack | Role |
| :--- | :--- | :--- |
| **Ingestion** | `BeautifulSoup` + `Feedparser` | Scrapes 50+ localized news sources every 5 mins. |
| **Intelligence** | `HuggingFace Transformers` | Runs **DistilBART** for context-aware risk scoring. |
| **Analysis** | `Scikit-Learn` | Runs **K-Means Clustering** for topic detection. |
| **Forecasting** | `NumPy` | Runs **Linear Regression** to calculate Risk Velocity. |
| **Storage** | `SQLite` | Lightweight, serverless storage for history & trends. |
| **UI** | `Streamlit` | Interactive frontend for mapping and metrics. |

---

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone [
cd astracode
2. Set up Virtual EnvironmentBash# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
3. Install DependenciesBashpip install -r requirements.txt
4. Run the ApplicationBashstreamlit run app.py

The dashboard will open automatically in your browser at http://localhost:8501
**🧠 The Science Behind the Code**
**1.The Risk Score (R)**
We don't trust AI blindly. We use a Hybrid Evaluation Model:
R = (Base Severity) + (AI Confidence x Amplifier)
Example: A "Riot" (Base 80) is always prioritized over "Inflation" (Base 50), ensuring critical safety alerts are never missed.

**2. The Stability Score (S)**
A macro-metric for national health:
S = 100 - (Weighted Avg Risk x Velocity Factor)
Stability drops faster if multiple risk events happen in a short time window.

**3. Forecasting Logic**
We treat risk scores over time as a scatter plot.
We calculate the Slope (m) of the best-fit line using Linear Regression.
If m > 0.5: The crisis is accelerating. Alert Triggered.

├── config/
│   ├── locations.json       # Dictionary for City-to-GPS mapping
│   └── config.json          # Risk thresholds and API keys
├── src/
│   ├── app.py               # Main Streamlit Frontend
│   ├── engine.py            # AI & NLP Logic (DistilBART)
│   ├── analytics.py         # Math & Forecasting (K-Means, Regression)
│   ├── database.py          # SQLite Manager
│   └── pipeline.py          # Data Scraper
├── requirements.txt         # Python Dependencies
└── README.md                # Documentation
🤝 ContributionThis project was developed for [MODEL-X HACKATHON].
