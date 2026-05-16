"""
Reusable functions for scraping and cleaning Google Play reviews.

Typical usage:
    raw = scrape_all()
    clean = preprocess_reviews(raw)
    clean.to_csv('data/raw/bank_reviews_clean.csv', index=False)
"""

import logging
import re
import time

import pandas as pd

log = logging.getLogger(__name__)


# Dashen has two app IDs because it migrated from com.cr2.amolelight to a new
# super-app. Both are scraped and combined so historical reviews aren't lost.
BANK_APP_IDS = {
    "Commercial Bank of Ethiopia": "com.combanketh.mobilebanking",
    "Bank of Abyssinia":           "com.boa.boaMobileBanking",
    "Dashen Bank":                 ["com.dashen.dashensuperapp", "com.cr2.amolelight"],
}


def scrape_reviews(app_id: str, bank_name: str, count: int = 500,
                   lang: str = 'en', country: str = 'et') -> pd.DataFrame:
    """
    Scrape Play Store reviews for one app and return a raw DataFrame.

    Returns an empty DataFrame (not an exception) on network or API errors so
    scrape_all() can continue with the remaining banks.
    """
    from google_play_scraper import reviews, Sort
    try:
        result, _ = reviews(app_id, lang=lang, country=country,
                            sort=Sort.NEWEST, count=count)
        df = pd.DataFrame(result)
        df['bank']   = bank_name
        df['source'] = 'Google Play'
        log.info("[%s] scraped %d reviews from %s", bank_name, len(df), app_id)
        return df
    except Exception as exc:
        log.warning("[%s] scrape failed for %s: %s", bank_name, app_id, exc)
        return pd.DataFrame()


def scrape_all(banks: dict = None, count_per_bank: int = 500,
               sleep_seconds: float = 1.0) -> pd.DataFrame:
    """
    Scrape all banks and return a combined raw DataFrame.

    sleep_seconds throttles requests to avoid Play Store rate limiting.
    """
    if banks is None:
        banks = BANK_APP_IDS
    frames = []
    for bank_name, app_ids in banks.items():
        ids = app_ids if isinstance(app_ids, list) else [app_ids]
        for app_id in ids:
            df = scrape_reviews(app_id, bank_name, count=count_per_bank)
            if not df.empty:
                frames.append(df)
            time.sleep(sleep_seconds)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def clean_text(text) -> str:
    """Collapse internal whitespace and strip leading/trailing spaces."""
    if pd.isna(text):
        return ''
    return re.sub(r'\s+', ' ', str(text)).strip()


def preprocess_reviews(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Transform raw scraper output into the canonical five-column format.

    Cleaning steps applied in order:
      1. Rename scraper columns → review, rating, date, bank, source
      2. Normalise whitespace in review text
      3. Drop rows with missing review or rating
      4. Drop rows where review is blank after stripping
      5. Drop duplicate (review, bank) pairs
      6. Parse dates to YYYY-MM-DD; unparseable dates become NaT (kept)
      7. Drop ratings outside 1-5 (scraper occasionally returns 0)
    """
    df = raw[['content', 'score', 'at', 'bank', 'source']].copy()
    df.columns = ['review', 'rating', 'date', 'bank', 'source']

    df['review'] = df['review'].apply(clean_text)
    df = df.dropna(subset=['review', 'rating'])
    df = df[df['review'].str.strip() != '']
    df = df.drop_duplicates(subset=['review', 'bank'])
    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.strftime('%Y-%m-%d')
    df = df[df['rating'].between(1, 5)]

    return df.reset_index(drop=True)
