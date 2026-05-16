"""
Reusable NLP functions for sentiment scoring and thematic analysis.
"""

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer


THEME_KEYWORDS = {
    'Transaction Performance': [
        'transfer', 'fast', 'slow', 'transaction', 'payment', 'speed',
        'quick', 'delay', 'processing', 'send', 'money', 'transfer money',
    ],
    'App Stability & Technical Issues': [
        'crash', 'error', 'bug', 'update', 'working', 'work', 'fix',
        'problem', 'issue', 'loading', 'open', 'force close', 'not working',
        'stop', 'fail', 'failed',
    ],
    'User Experience & Design': [
        'interface', 'easy', 'design', 'navigation', 'ui', 'layout',
        'user friendly', 'simple', 'clean', 'nice', 'beautiful', 'good',
        'great', 'excellent', 'amazing', 'love', 'best', 'helpful', 'useful',
    ],
    'Account & Security': [
        'login', 'password', 'otp', 'fingerprint', 'biometric', 'account',
        'access', 'pin', 'secure', 'security', 'authentication', 'verify',
    ],
    'Customer Support': [
        'support', 'response', 'call', 'service', 'help', 'staff',
        'customer service', 'contact', 'feedback', 'solve', 'resolved',
    ],
}


def score_sentiment_vader(texts: pd.Series) -> pd.DataFrame:
    """
    Apply VADER sentiment analysis to a Series of review texts.

    Returns a DataFrame with columns: sentiment_score, sentiment_label.
    """
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    analyzer = SentimentIntensityAnalyzer()

    def _score(text):
        if pd.isna(text) or str(text).strip() == '':
            return 0.0, 'neutral'
        compound = analyzer.polarity_scores(str(text))['compound']
        if compound >= 0.05:
            label = 'positive'
        elif compound <= -0.05:
            label = 'negative'
        else:
            label = 'neutral'
        return round(compound, 4), label

    results = texts.apply(lambda x: pd.Series(_score(x),
                                               index=['sentiment_score', 'sentiment_label']))
    return results


def assign_theme(text: str, theme_keywords: dict = None) -> str:
    """Map a review to the best-matching theme using keyword counts."""
    if theme_keywords is None:
        theme_keywords = THEME_KEYWORDS
    if pd.isna(text):
        return 'General Feedback'
    text_lower = str(text).lower()
    scores = {theme: sum(1 for kw in kws if kw in text_lower)
              for theme, kws in theme_keywords.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else 'General Feedback'


def extract_top_keywords(reviews: pd.Series, n: int = 15) -> list[tuple]:
    """
    Return the top-n TF-IDF keywords (word, score) for a collection of reviews.
    """
    if len(reviews.dropna()) < 2:
        return []
    vectorizer = TfidfVectorizer(
        max_features=50,
        stop_words='english',
        ngram_range=(1, 2),
        min_df=2,
    )
    try:
        X = vectorizer.fit_transform(reviews.dropna())
        scores = X.sum(axis=0).A1
        words = vectorizer.get_feature_names_out()
        top_idx = scores.argsort()[::-1][:n]
        return [(words[i], round(scores[i], 3)) for i in top_idx]
    except ValueError:
        return []


def run_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply sentiment scoring and theme assignment to a clean reviews DataFrame.

    Expects columns: review, rating, date, bank, source.
    Returns the same DataFrame with additional columns added in place.
    """
    sentiment = score_sentiment_vader(df['review'])
    df['sentiment_score'] = sentiment['sentiment_score']
    df['sentiment_label'] = sentiment['sentiment_label']
    df['identified_theme'] = df['review'].apply(assign_theme)
    return df
