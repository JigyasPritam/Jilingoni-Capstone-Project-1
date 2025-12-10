# early_risk_pipeline.py
import argparse
import os
import pandas as pd
from risk_utils import compute_flags
import matplotlib.pyplot as plt

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def load_data(path):
    if path.lower().endswith(('.xls', '.xlsx')):
        return pd.read_excel(path)
    elif path.lower().endswith('.csv'):
        return pd.read_csv(path)
    else:
        raise ValueError("Unsupported file type. Use .csv or .xlsx")

def save_csv(df, outdir, name='early_risk_results.csv'):
    ensure_dir(outdir)
    outpath = os.path.join(outdir, name)
    df.to_csv(outpath, index=False)
    return outpath

def basic_plots(df, outdir):
    ensure_dir(outdir)
    # Utilisation histogram
    if 'Utilisation %' in df.columns:
        plt.figure(figsize=(7,4))
        plt.hist(df['Utilisation %'].dropna(), bins=30)
        plt.title('Distribution of Utilisation %')
        plt.xlabel('Utilisation %')
        plt.ylabel('Count')
        plt.tight_layout()
        plt.savefig(os.path.join(outdir, 'hist_utilisation.png'))
        plt.close()

    # Risk tier counts
    if 'risk_tier' in df.columns:
        counts = df['risk_tier'].value_counts().reindex(['Low','Medium','High'], fill_value=0)
        plt.figure(figsize=(6,4))
        plt.bar(counts.index.astype(str), counts.values)
        plt.title('Count by Risk Tier')
        plt.xlabel('Risk Tier')
        plt.ylabel('Count')
        plt.tight_layout()
        plt.savefig(os.path.join(outdir, 'bar_risk_tier_count.png'))
        plt.close()

def run_pipeline(input_path, outdir):
    print("Loading data:", input_path)
    df = load_data(input_path)
    print("Computing flags...")
    df = compute_flags(df)
    out_csv = save_csv(df, outdir)
    print("Saved results to:", out_csv)
    print("Generating basic plots...")
    basic_plots(df, outdir)
    print("Plots saved to:", outdir)
    # Print top risky customers to console
    top = df.sort_values('risk_score', ascending=False).head(20)
    print("Top flagged customers (preview):")
    cols = ['Customer ID','risk_score','risk_tier','reasons','Utilisation %','Avg Payment Ratio','Min Due Paid Frequency','Cash Withdrawal %','DPD Bucket Next Month']
    cols = [c for c in cols if c in top.columns]
    print(top[cols].to_string(index=False))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Early Risk pipeline")
    parser.add_argument('--input', '-i', required=True, help='Input CSV/XLSX path')
    parser.add_argument('--outdir', '-o', default='./outputs', help='Output directory')
    args = parser.parse_args()
    run_pipeline(args.input, args.outdir)
