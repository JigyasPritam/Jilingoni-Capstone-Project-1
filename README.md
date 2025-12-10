# Early Risk Signals – Credit Card Delinquency Watch

This project provides a lightweight, explainable risk-flagging system to identify early warning signals in credit card customers. It processes CSV/XLSX files, computes rule-based risk scores, and displays results in a dashboard UI.

------------------------------------
## Overview
------------------------------------

The system follows this flow:

1. User uploads a CSV/XLSX file from the frontend.
2. Backend (Flask) reads the file and computes:
   - Rule-based early risk flags
   - Risk score (0–5)
   - Risk tier (Low / Medium / High)
   - Human-readable reasons for each flagged risk
3. Backend returns JSON.
4. Frontend renders:
   - Risk tier counts
   - High / Medium / Low risk tables
   - Customer-level explanations

This project is built for use cases in fintech analytics, banking risk teams, hackathons, and academic research.

------------------------------------
## Project Structure
------------------------------------

.
├── risk_utils.py                # Core feature engineering and flag generation
├── early_risk_pipeline.py       # CLI batch processing (offline analysis)
├── server.py                    # Flask backend (upload → JSON output)
├── index.html                   # Dashboard UI (upload + results)
├── requirements.txt             # Python dependencies
└── Dockerfile (optional)        # Containerized deployment

------------------------------------
## Installation
------------------------------------

1. Clone repository:  
   git clone https://github.com/JigyasPritam/Jilingoni-Capstone-Project-1.git  
   cd Jilingoni-Capstone-Project-1

2. Install dependencies:
   pip install -r requirements.txt

------------------------------------
## Running the Backend
------------------------------------

Start the Flask server:

   python server.py

API endpoint:
   http://localhost:5000/upload

------------------------------------
## Running the Frontend Dashboard
------------------------------------

Option 1: Open index.html directly in the browser.

Option 2: Serve with a simple HTTP server:

   python -m http.server 8080

Access:
   http://localhost:8080/index.html

------------------------------------
## Expected Input Columns
------------------------------------

The uploaded CSV/XLSX should contain:

- Customer ID
- Credit Limit
- Utilisation %
- Avg Payment Ratio (0–1 or 0–100)
- Min Due Paid Frequency
- Merchant Mix Index (0–1 or 0–100)
- Cash Withdrawal %
- Recent Spend Change %
- Current DPD Bucket (optional)
- DPD Bucket Next Month (optional)

Missing columns are handled safely with default values.

------------------------------------
## Risk Rules (Explainable Logic)
------------------------------------

A customer is flagged based on the following rule-based signals:

1. Utilisation Spike:
   Utilisation % >= 80 AND Recent Spend Change >= 20

2. Minimum Due Streak:
   Min Due Paid Frequency >= 2

3. Low Payment Ratio:
   Avg Payment Ratio <= 0.4

4. Cash Advance Distress:
   Cash Withdrawal % > 0 AND Utilisation % > 70

5. Merchant Mix Shift:
   Merchant Mix Index <= 0.35 after normalization

Risk Score = number of flags triggered

Risk Tier:
- 0 → Low
- 1 → Medium
- 2 or more → High

------------------------------------
## Future Enhancements
------------------------------------

- Add interactive charts using Chart.js
- Streamlit dashboard version
- PostgreSQL integration for storing historical uploads
- WebSocket real-time updates
- ML model (XGBoost) for predictive scoring + SHAP explainability

