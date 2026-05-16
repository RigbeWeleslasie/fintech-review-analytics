"""
Reusable NLP functions for sentiment scoring and thematic analysis of bank reviews.

Pipeline order: score_sentiment_vader → assign_theme → extract_top_keywords
Entry point for batch processing: run_pipeline()
"""

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer


# Keywords are checked as substrings so multi-word phrases (e.g. "not working")
# match naturally. The first theme whose keyword count is highest wins; ties go
# to the first theme in insertion order. Reviews with zero matches fall through
# to 'General Feedback'.
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
    Score each review with VADER and return a DataFrame with two new columns.

    Thresholds follow VADER's recommended boundaries:
      compound >= 0.05  → positive
      compound <= -0.05 → negative
      otherwise         → neutral
    Empty or NaN texts are assigned score=0.0 / label='neutral' rather than
    raising an error, so the pipeline handles partially-complete datasets.
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

    return texts.apply(
        lambda x: pd.Series(_score(x), index=['sentiment_score', 'sentiment_label'])
    )


def assign_theme(text: str, theme_keywords: dict = None) -> str:
    """
    Map a review to the best-matching business theme via keyword counting.

    Each theme's score is the number of its keywords found in the lowercased
    text. The theme with the highest score wins. Falls back to 'General
    Feedback' when no keywords match (e.g. very short or non-English reviews).
    """
    if theme_keywords is None:
        theme_keywords = THEME_KEYWORDS
    if pd.isna(text):
        return 'General Feedback'
    text_lower = str(text).lower()
    scores = {
        theme: sum(1 for kw in kws if kw in text_lower)
        for theme, kws in theme_keywords.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else 'General Feedback'


def extract_top_keywords(reviews: pd.Series, n: int = 15) -> list[tuple]:
    """
    Return the top-n TF-IDF (term, score) pairs for a collection of reviews.

    Uses unigrams + bigrams with min_df=2 so single-occurrence noise is
    filtered out. Returns an empty list when there are fewer than 2 non-null
    reviews (TfidfVectorizer requires at least 2 documents).
    """
    clean = reviews.dropna()
    if len(clean) < 2:
        return []
    vectorizer = TfidfVectorizer(
        max_features=50,
        stop_words='english',
        ngram_range=(1, 2),
        min_df=2,
    )
    try:
        X = vectorizer.fit_transform(clean)
        # Sum TF-IDF scores across all documents to rank corpus-wide importance
        corpus_scores = X.sum(axis=0).A1
        words = vectorizer.get_feature_names_out()
        top_idx = corpus_scores.argsort()[::-1][:n]
        return [(words[i], round(corpus_scores[i], 3)) for i in top_idx]
    except ValueError:
        return []


def run_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply full NLP pipeline to a clean reviews DataFrame.

    Expects columns: review, rating, date, bank, source.
    Adds in place: sentiment_score, sentiment_label, identified_theme.
    """
    sentiment = score_sentiment_vader(df['review'])
    df = df.copy()
    df['sentiment_score'] = sentiment['sentiment_score']
    df['sentiment_label'] = sentiment['sentiment_label']
    df['identified_theme'] = df['review'].apply(assign_theme)
    return df
