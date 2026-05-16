"""
Standalone preprocessing script for Ethiopian bank Google Play reviews.

Usage:
    python scripts/preprocess.py

Outputs:
    data/raw/bank_reviews_clean.csv
"""

import pandas as pd
import numpy as np
import re
import os
import time
import warnings

warnings.filterwarnings('ignore')

# ── Target apps ──────────────────────────────────────────────────────────────
BANKS = {
    "Commercial Bank of Ethiopia": "com.combanketh.mobilebanking",
    "Bank of Abyssinia":           "com.boa.boaMobileBanking",
    # Dashen migrated to the Super App; fallback to legacy ID if needed
    "Dashen Bank":                 ["com.dashen.dashensuperapp", "com.cr2.amolelight"],
}

TARGET_PER_BANK = 500
OUTPUT_PATH     = "data/raw/bank_reviews_clean.csv"


def clean_text(text: str) -> str:
    if pd.isna(text):
        return ""
    text = str(text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def scrape_bank(app_id: str, bank_name: str, count: int = 500) -> pd.DataFrame:
    from google_play_scraper import reviews, Sort
    try:
        result, _ = reviews(
            app_id,
            lang='en',
            country='et',
            sort=Sort.NEWEST,
            count=count,
        )
        df = pd.DataFrame(result)
        df['bank']   = bank_name
        df['source'] = 'Google Play'
        print(f"  [{bank_name}] Scraped {len(df)} reviews from {app_id}")
        return df
    except Exception as exc:
        print(f"  [{bank_name}] Failed ({app_id}): {exc}")
        return pd.DataFrame()


def scrape_all_banks() -> pd.DataFrame:
    frames = []
    for bank_name, app_ids in BANKS.items():
        ids = app_ids if isinstance(app_ids, list) else [app_ids]
        bank_frames = []
        for app_id in ids:
            df = scrape_bank(app_id, bank_name, count=TARGET_PER_BANK)
            if not df.empty:
                bank_frames.append(df)
            time.sleep(1)   # polite delay between requests
        if bank_frames:
            frames.append(pd.concat(bank_frames, ignore_index=True))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def preprocess(raw: pd.DataFrame) -> pd.DataFrame:
    # Keep only required columns
    df = raw[['content', 'score', 'at', 'bank', 'source']].copy()
    df.columns = ['review', 'rating', 'date', 'bank', 'source']

    # Clean text
    df['review'] = df['review'].apply(clean_text)

    # Drop rows with missing review text or rating
    before = len(df)
    df = df.dropna(subset=['review', 'rating'])
    df = df[df['review'].str.strip() != '']
    after_drop = len(df)
    print(f"  Dropped {before - after_drop} rows missing review text or rating")

    # Remove duplicates
    before_dedup = len(df)
    df = df.drop_duplicates(subset=['review', 'bank'])
    print(f"  Removed {before_dedup - len(df)} duplicate reviews")

    # Normalise dates
    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.strftime('%Y-%m-%d')

    # Validate rating range
    df = df[df['rating'].between(1, 5)]

    return df.reset_index(drop=True)


def main():
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.makedirs('data/raw', exist_ok=True)

    print("=" * 55)
    print("  Ethiopian Bank Review Scraper & Preprocessor")
    print("=" * 55)

    print("\nStep 1: Scraping reviews...")
    raw = scrape_all_banks()

    if raw.empty:
        print("ERROR: No reviews collected. Check internet connection and app IDs.")
        return

    print(f"\n  Raw reviews collected: {len(raw)}")

    print("\nStep 2: Preprocessing...")
    clean = preprocess(raw)

    print(f"\n  Final dataset: {len(clean)} reviews")
    print("\nReviews per bank:")
    print(clean['bank'].value_counts().to_string())

    clean.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved to: {OUTPUT_PATH}")

    # Data quality report
    print("\n" + "=" * 55)
    print("  DATA QUALITY REPORT")
    print("=" * 55)
    print(f"  Total reviews    : {len(clean)}")
    print(f"  Missing values   : {clean.isnull().sum().sum()}")
    print(f"  Date range       : {clean['date'].min()} → {clean['date'].max()}")
    print(f"  Rating range     : {clean['rating'].min()} – {clean['rating'].max()}")
    for bank in clean['bank'].unique():
        n = len(clean[clean['bank'] == bank])
        status = '✓' if n >= 400 else '✗ BELOW MINIMUM'
        print(f"  {bank:40s}: {n:4d} reviews  {status}")


if __name__ == '__main__':
    main()
