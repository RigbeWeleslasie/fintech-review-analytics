"""
Unit tests for src/sentiment_analyzer.py

These tests exercise the NLP logic directly without touching the CSV, so they
run in CI even when the real data file is gitignored.
"""

import pandas as pd
import pytest
from src.sentiment_analyzer import (
    assign_theme,
    extract_top_keywords,
    score_sentiment_vader,
    run_pipeline,
    THEME_KEYWORDS,
)


# ---------------------------------------------------------------------------
# score_sentiment_vader
# ---------------------------------------------------------------------------

def test_positive_review_labelled_positive():
    texts = pd.Series(["I love this app, it is amazing and works perfectly!"])
    result = score_sentiment_vader(texts)
    assert result.iloc[0]['sentiment_label'] == 'positive'


def test_negative_review_labelled_negative():
    texts = pd.Series(["This app is terrible. It crashes constantly and never works."])
    result = score_sentiment_vader(texts)
    assert result.iloc[0]['sentiment_label'] == 'negative'


def test_neutral_review_labelled_neutral():
    # A factual statement with no strong sentiment words sits near zero
    texts = pd.Series(["The app has a login screen."])
    result = score_sentiment_vader(texts)
    assert result.iloc[0]['sentiment_label'] in ('neutral', 'positive', 'negative')


def test_sentiment_score_within_vader_range():
    texts = pd.Series([
        "Great app!",
        "Terrible experience.",
        "It exists.",
    ])
    result = score_sentiment_vader(texts)
    assert result['sentiment_score'].between(-1.0, 1.0).all()


def test_empty_text_returns_neutral():
    texts = pd.Series(["", "   "])
    result = score_sentiment_vader(texts)
    assert (result['sentiment_label'] == 'neutral').all()
    assert (result['sentiment_score'] == 0.0).all()


def test_nan_text_returns_neutral():
    texts = pd.Series([None, float('nan')])
    result = score_sentiment_vader(texts)
    assert (result['sentiment_label'] == 'neutral').all()


def test_returns_two_columns():
    result = score_sentiment_vader(pd.Series(["hello"]))
    assert set(result.columns) == {'sentiment_score', 'sentiment_label'}


# ---------------------------------------------------------------------------
# assign_theme
# ---------------------------------------------------------------------------

def test_transaction_keyword_maps_to_transaction_theme():
    assert assign_theme("The transfer was very slow and had a delay") == 'Transaction Performance'


def test_crash_keyword_maps_to_stability_theme():
    assert assign_theme("App keeps crashing and showing error messages") == 'App Stability & Technical Issues'


def test_login_keyword_maps_to_security_theme():
    assert assign_theme("I cannot login, the OTP never arrives") == 'Account & Security'


def test_support_keyword_maps_to_customer_support_theme():
    assert assign_theme("Customer service did not respond to my call") == 'Customer Support'


def test_ux_keyword_maps_to_ux_theme():
    assert assign_theme("The interface is clean and easy to navigate") == 'User Experience & Design'


def test_no_keyword_falls_back_to_general_feedback():
    assert assign_theme("xyz qrs abc 123") == 'General Feedback'


def test_nan_input_returns_general_feedback():
    assert assign_theme(float('nan')) == 'General Feedback'
    assert assign_theme(None) == 'General Feedback'


def test_custom_theme_keywords_respected():
    custom = {'TestTheme': ['unicorn', 'rainbow']}
    assert assign_theme("I saw a unicorn today", theme_keywords=custom) == 'TestTheme'


def test_theme_keywords_dict_covers_expected_themes():
    expected = {
        'Transaction Performance',
        'App Stability & Technical Issues',
        'User Experience & Design',
        'Account & Security',
        'Customer Support',
    }
    assert expected.issubset(set(THEME_KEYWORDS.keys()))


# ---------------------------------------------------------------------------
# extract_top_keywords
# ---------------------------------------------------------------------------

def test_returns_list_of_tuples():
    reviews = pd.Series(["fast transfer payment"] * 5 + ["slow app crash"] * 5)
    result = extract_top_keywords(reviews, n=5)
    assert isinstance(result, list)
    assert all(isinstance(item, tuple) and len(item) == 2 for item in result)


def test_returns_at_most_n_keywords():
    reviews = pd.Series(["fast payment transfer"] * 10)
    result = extract_top_keywords(reviews, n=3)
    assert len(result) <= 3


def test_returns_empty_list_for_too_few_reviews():
    assert extract_top_keywords(pd.Series(["only one review"]), n=5) == []
    assert extract_top_keywords(pd.Series([None, None]), n=5) == []


def test_scores_are_positive_floats():
    reviews = pd.Series(["great app very useful"] * 10)
    result = extract_top_keywords(reviews, n=5)
    for _, score in result:
        assert isinstance(score, float)
        assert score > 0


# ---------------------------------------------------------------------------
# run_pipeline
# ---------------------------------------------------------------------------

def test_run_pipeline_adds_required_columns():
    df = pd.DataFrame({
        'review': ["Great app!", "Terrible crash.", "Login failed."],
        'rating': [5, 1, 2],
        'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'bank': ['CBE', 'BOA', 'Dashen'],
        'source': ['Google Play'] * 3,
    })
    result = run_pipeline(df)
    assert 'sentiment_score' in result.columns
    assert 'sentiment_label' in result.columns
    assert 'identified_theme' in result.columns


def test_run_pipeline_does_not_drop_rows():
    df = pd.DataFrame({
        'review': ["Good app"] * 5,
        'rating': [4] * 5,
        'date': ['2024-01-01'] * 5,
        'bank': ['CBE'] * 5,
        'source': ['Google Play'] * 5,
    })
    result = run_pipeline(df)
    assert len(result) == 5


def test_run_pipeline_does_not_mutate_input():
    df = pd.DataFrame({
        'review': ["Nice app"],
        'rating': [5],
        'date': ['2024-01-01'],
        'bank': ['CBE'],
        'source': ['Google Play'],
    })
    original_cols = list(df.columns)
    run_pipeline(df)
    assert list(df.columns) == original_cols
