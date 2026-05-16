"""
Standalone scraping and preprocessing script for Ethiopian bank Google Play reviews.

Usage:
    python scripts/preprocess.py
    python scripts/preprocess.py --count 300 --lang en --country et --output data/raw/out.csv

Arguments:
    --count   Reviews to request per bank app (default: 500)
    --lang    Review language code            (default: en)
    --country Store country code              (default: et)
    --output  Destination CSV path            (default: data/raw/bank_reviews_clean.csv)

Outputs:
    CSV with columns: review, rating, date, bank, source
"""

import argparse
import logging
import os
import re
import time

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# Dashen has two app IDs — it migrated from the legacy app to a super-app.
# Both are scraped so historical reviews are not lost.
BANKS = {
    "Commercial Bank of Ethiopia": "com.combanketh.mobilebanking",
    "Bank of Abyssinia":           "com.boa.boaMobileBanking",
    "Dashen Bank":                 ["com.dashen.dashensuperapp", "com.cr2.amolelight"],
}

DEFAULT_OUTPUT = "data/raw/bank_reviews_clean.csv"


def clean_text(text: str) -> str:
    """Collapse internal whitespace and strip leading/trailing spaces."""
    if pd.isna(text):
        return ""
    return re.sub(r'\s+', ' ', str(text)).strip()


def scrape_bank(app_id: str, bank_name: str, count: int,
                lang: str, country: str) -> pd.DataFrame:
    """
    Scrape Play Store reviews for one app.

    Returns an empty DataFrame (instead of raising) on network or API errors
    so the caller can continue with the remaining banks.
    """
    from google_play_scraper import reviews, Sort
    try:
        result, _ = reviews(
            app_id, lang=lang, country=country,
            sort=Sort.NEWEST, count=count,
        )
        df = pd.DataFrame(result)
        df['bank']   = bank_name
        df['source'] = 'Google Play'
        log.info("[%s] scraped %d reviews from %s", bank_name, len(df), app_id)
        return df
    except Exception as exc:
        log.warning("[%s] scrape failed for %s: %s", bank_name, app_id, exc)
        return pd.DataFrame()


def scrape_all_banks(count: int, lang: str, country: str) -> pd.DataFrame:
    """Scrape all banks and return a combined raw DataFrame."""
    frames = []
    for bank_name, app_ids in BANKS.items():
        ids = app_ids if isinstance(app_ids, list) else [app_ids]
        for app_id in ids:
            df = scrape_bank(app_id, bank_name, count=count,
                             lang=lang, country=country)
            if not df.empty:
                frames.append(df)
            time.sleep(1)   # polite delay to avoid Play Store rate limiting
    if not frames:
        raise RuntimeError("No reviews collected — check internet connection and app IDs.")
    return pd.concat(frames, ignore_index=True)


def preprocess(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Transform raw scraper output into the canonical five-column format.

    Steps:
      1. Rename columns → review, rating, date, bank, source
      2. Normalise whitespace in review text
      3. Drop rows missing review text or rating
      4. Drop blank reviews (empty after stripping)
      5. Remove duplicate (review, bank) pairs
      6. Normalise dates to YYYY-MM-DD
      7. Drop ratings outside 1-5
    """
    df = raw[['content', 'score', 'at', 'bank', 'source']].copy()
    df.columns = ['review', 'rating', 'date', 'bank', 'source']

    df['review'] = df['review'].apply(clean_text)

    before = len(df)
    df = df.dropna(subset=['review', 'rating'])
    df = df[df['review'].str.strip() != '']
    log.info("dropped %d rows missing review text or rating", before - len(df))

    before_dedup = len(df)
    df = df.drop_duplicates(subset=['review', 'bank'])
    log.info("removed %d duplicate reviews", before_dedup - len(df))

    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.strftime('%Y-%m-%d')
    df = df[df['rating'].between(1, 5)]

    return df.reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scrape and preprocess Google Play reviews for Ethiopian banks."
    )
    parser.add_argument("--count",   type=int, default=500,
                        help="Reviews to request per bank app (default: 500)")
    parser.add_argument("--lang",    default="en",
                        help="Review language code (default: en)")
    parser.add_argument("--country", default="et",
                        help="Store country code (default: et)")
    parser.add_argument("--output",  default=DEFAULT_OUTPUT,
                        help=f"Destination CSV path (default: {DEFAULT_OUTPUT})")
    args = parser.parse_args()

    # Run from project root so relative paths (data/raw/) resolve correctly
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    log.info("=== Ethiopian Bank Review Scraper & Preprocessor ===")
    log.info("count=%d  lang=%s  country=%s", args.count, args.lang, args.country)

    log.info("Step 1: scraping reviews...")
    raw = scrape_all_banks(count=args.count, lang=args.lang, country=args.country)
    log.info("raw reviews collected: %d", len(raw))

    log.info("Step 2: preprocessing...")
    clean = preprocess(raw)
    log.info("final dataset: %d reviews", len(clean))

    clean.to_csv(args.output, index=False)
    log.info("saved to: %s", args.output)

    log.info("=== DATA QUALITY REPORT ===")
    log.info("total reviews  : %d", len(clean))
    log.info("missing values : %d", clean.isnull().sum().sum())
    log.info("date range     : %s -> %s", clean['date'].min(), clean['date'].max())
    log.info("rating range   : %s - %s", clean['rating'].min(), clean['rating'].max())
    for bank in clean['bank'].unique():
        n = len(clean[clean['bank'] == bank])
        status = "OK" if n >= 400 else "BELOW MINIMUM"
        log.info("  %-40s : %4d reviews  [%s]", bank, n, status)


if __name__ == '__main__':
    main()
