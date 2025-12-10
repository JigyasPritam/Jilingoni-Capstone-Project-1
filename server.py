# server.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import io

app = Flask(__name__)
CORS(app)

# -----------------------------
# Helper: Normalize merchant mix
# -----------------------------
def normalize_merchant_mix(series: pd.Series) -> pd.Series:
    if series.isnull().all():
        return series
    s = series.copy().astype(float)
    if s.max(skipna=True) > 1.5:
        s = s / 100.0
    return s.clip(lower=0.0, upper=1.0)

# -----------------------------
# Compute rule-based flags
# -----------------------------
def compute_flags(df: pd.DataFrame) -> pd.DataFrame:

    # Ensure numeric conversion
    numeric_cols = [
        'Utilisation %', 'Avg Payment Ratio', 'Min Due Paid Frequency',
        'Cash Withdrawal %', 'Recent Spend Change %'
    ]

    for c in numeric_cols:
        if c not in df.columns:
            df[c] = np.nan
        df[c] = pd.to_numeric(df[c], errors='coerce')

    # Merchant mix handling
    if 'Merchant Mix Index' in df.columns:
        df['MerchantMix_norm'] = normalize_merchant_mix(df['Merchant Mix Index'])
    else:
        df['MerchantMix_norm'] = np.nan

    # Avg Payment Ratio scaling
    if df['Avg Payment Ratio'].max(skipna=True) > 1.5:
        df['Avg Payment Ratio'] = df['Avg Payment Ratio'] / 100.0
    df['Avg Payment Ratio'] = df['Avg Payment Ratio'].clip(0, 1).fillna(0)

    # Flags
    df['flag_util_spike'] = (
        (df['Utilisation %'].fillna(0) >= 80) &
        (df['Recent Spend Change %'].fillna(0) >= 20)
    ).astype(int)

    df['flag_min_due_streak'] = (df['Min Due Paid Frequency'].fillna(0) >= 2).astype(int)

    df['flag_low_pay_ratio'] = (df['Avg Payment Ratio'].fillna(1) <= 0.4).astype(int)

    df['flag_cash_advance'] = (
        (df['Cash Withdrawal %'].fillna(0) > 0) &
        (df['Utilisation %'].fillna(0) > 70)
    ).astype(int)

    df['flag_merchant_shift'] = (df['MerchantMix_norm'].fillna(1) <= 0.35).astype(int)

    flag_cols = [
        'flag_util_spike', 'flag_min_due_streak', 'flag_low_pay_ratio',
        'flag_cash_advance', 'flag_merchant_shift'
    ]

    df['risk_score'] = df[flag_cols].sum(axis=1)
    df['risk_tier'] = pd.cut(df['risk_score'], [-1,0,1,999], labels=['Low', 'Medium', 'High'])

    # Reasons
    def get_reasons(row):
        r = []
        if row['flag_util_spike']: r.append("Util Spike")
        if row['flag_min_due_streak']: r.append("Min Due Streak")
        if row['flag_low_pay_ratio']: r.append("Low Payment Ratio")
        if row['flag_cash_advance']: r.append("Cash Advance")
        if row['flag_merchant_shift']: r.append("Merchant Mix Shift")
        return ", ".join(r) if r else "None"

    df['reasons'] = df.apply(get_reasons, axis=1)

    return df

# -----------------------------
# API: Upload CSV/XLSX → Process → Return JSON
# -----------------------------
@app.route("/upload", methods=["POST"])
def upload_file():

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Empty file name"}), 400

    # Try read CSV, then Excel
    try:
        stream = io.BytesIO(file.read())
        stream.seek(0)
        try:
            df = pd.read_csv(stream)
        except Exception:
            stream.seek(0)
            df = pd.read_excel(stream)
    except Exception as e:
        return jsonify({"error": f"Could not read file: {str(e)}"}), 400

    # Process the dataframe
    try:
        df = compute_flags(df)
    except Exception as e:
        return jsonify({"error": f"Processing error: {str(e)}"}), 500

    # Output subset for dashboard
    cols = [
        "Customer ID", "risk_score", "risk_tier", "reasons",
        "Utilisation %", "Avg Payment Ratio", "Min Due Paid Frequency",
        "Cash Withdrawal %"
    ]
    cols = [c for c in cols if c in df.columns]

    out = df[cols].copy()

    # Convert NaN → None so JSON is always valid
    out = out.where(pd.notnull(out), None)

    # Convert to Python dict
    records = out.to_dict(orient="records")

    return jsonify({
        "count": len(records),
        "rows": records
    }), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)
