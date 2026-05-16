"""
Reusable functions for scraping and cleaning Google Play reviews.
"""

import re
import time
import pandas as pd


BANK_APP_IDS = {
    "Commercial Bank of Ethiopia": "com.combanketh.mobilebanking",
    "Bank of Abyssinia":           "com.boa.boaMobileBanking",
    "Dashen Bank":                 ["com.dashen.dashensuperapp", "com.cr2.amolelight"],
}


def scrape_reviews(app_id: str, bank_name: str, count: int = 500,
                   lang: str = 'en', country: str = 'et') -> pd.DataFrame:
    """Scrape Play Store reviews for a single app and return a raw DataFrame."""
    from google_play_scraper import reviews, Sort
    try:
        result, _ = reviews(app_id, lang=lang, country=country,
                            sort=Sort.NEWEST, count=count)
        df = pd.DataFrame(result)
        df['bank']   = bank_name
        df['source'] = 'Google Play'
        return df
    except Exception as exc:
        print(f"[{bank_name}] Scrape failed ({app_id}): {exc}")
        return pd.DataFrame()


def scrape_all(banks: dict = None, count_per_bank: int = 500,
               sleep_seconds: float = 1.0) -> pd.DataFrame:
    """Scrape all banks and return a combined raw DataFrame."""
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
    """Normalise whitespace and strip review text."""
    if pd.isna(text):
        return ''
    return re.sub(r'\s+', ' ', str(text)).strip()


def preprocess_reviews(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Transform raw scraper output into the canonical five-column format.

    Returns a DataFrame with columns: review, rating, date, bank, source.
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
