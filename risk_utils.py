# risk_utils.py
import pandas as pd
import numpy as np

REQUIRED_COLUMNS = [
    'Customer ID', 'Credit Limit', 'Utilisation %', 'Avg Payment Ratio',
    'Min Due Paid Frequency', 'Merchant Mix Index', 'Cash Withdrawal %',
    'Recent Spend Change %', 'DPD Bucket Next Month'
]

def normalize_merchant_mix(series: pd.Series) -> pd.Series:
    """Normalize Merchant Mix Index into 0-1 scale."""
    s = series.copy()
    if s.isnull().all():
        return s
    # If values are likely 0-100 scale (max > 1.5), scale down
    if s.max() > 1.5:
        s = s / 100.0
    # Clip to 0-1
    return s.clip(lower=0.0, upper=1.0)

def safe_load_defaults(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure required columns exist (fill missing optional ones with NaN or zeros
    for safe processing). Raises an error only for critical columns (if needed).
    """
    # Create missing columns with NaN (but we don't force Customer ID)
    for c in REQUIRED_COLUMNS:
        if c not in df.columns:
            df[c] = np.nan
    return df

def compute_flags(df: pd.DataFrame, merchant_col='Merchant Mix Index') -> pd.DataFrame:
    """
    Compute rule-based flags and risk score.
    Returns a copy of df with new columns:
      - flag_util_spike, flag_min_due_streak, flag_low_pay_ratio,
        flag_cash_advance, flag_merchant_shift, risk_score, risk_tier, reasons
    """
    df = df.copy()
    df = safe_load_defaults(df)

    # Normalize merchant mix
    df['MerchantMix_norm'] = normalize_merchant_mix(df[merchant_col])

    # Ensure numeric columns exist and coerce types
    numeric_cols = ['Utilisation %', 'Avg Payment Ratio', 'Min Due Paid Frequency',
                    'Cash Withdrawal %', 'Recent Spend Change %']
    for c in numeric_cols:
        if c not in df.columns:
            df[c] = 0.0
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0.0)

    # Clip/scale Avg Payment Ratio if in percentages
    if df['Avg Payment Ratio'].max() > 1.5:
        df['Avg Payment Ratio'] = df['Avg Payment Ratio'] / 100.0
    df['Avg Payment Ratio'] = df['Avg Payment Ratio'].clip(lower=0.0, upper=1.0)

    # ---- Flags (illustrative thresholds; tune after EDA) ----
    df['flag_util_spike'] = (
        (df['Utilisation %'] >= 80) &
        (df['Recent Spend Change %'] >= 20)
    ).astype(int)

    df['flag_min_due_streak'] = (df['Min Due Paid Frequency'] >= 2).astype(int)

    df['flag_low_pay_ratio'] = (df['Avg Payment Ratio'] <= 0.4).astype(int)

    df['flag_cash_advance'] = (
        (df['Cash Withdrawal %'] > 0) &
        (df['Utilisation %'] > 70)
    ).astype(int)

    df['flag_merchant_shift'] = (df['MerchantMix_norm'] <= 0.35).astype(int)

    flag_cols = [
        'flag_util_spike', 'flag_min_due_streak', 'flag_low_pay_ratio',
        'flag_cash_advance', 'flag_merchant_shift'
    ]

    df['risk_score'] = df[flag_cols].sum(axis=1)
    df['risk_tier'] = pd.cut(df['risk_score'], bins=[-1,0,1,999], labels=['Low','Medium','High'])

    # Make a readable "reasons" string for dashboards
    def reasons_for_row(row):
        reasons = []
        if row['flag_util_spike']: reasons.append('Util Spike')
        if row['flag_min_due_streak']: reasons.append('Min Due Streak')
        if row['flag_low_pay_ratio']: reasons.append('Low Payment Ratio')
        if row['flag_cash_advance']: reasons.append('Cash Advance')
        if row['flag_merchant_shift']: reasons.append('Merchant Mix Shift')
        return ', '.join(reasons) if reasons else 'None'

    df['reasons'] = df.apply(reasons_for_row, axis=1)

    # Binary target if target exists: rolled-forward (next > current)
    if 'Current DPD Bucket' in df.columns and not df['Current DPD Bucket'].isnull().all():
        df['target_positive'] = (df['DPD Bucket Next Month'].fillna(0) > df['Current DPD Bucket'].fillna(0)).astype(int)
    else:
        df['target_positive'] = (df['DPD Bucket Next Month'].fillna(0) != 0).astype(int)

    return df
