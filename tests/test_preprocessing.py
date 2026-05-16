"""
Unit tests for src/data_collector.py preprocessing functions.

Tests use synthetic DataFrames that mimic raw google-play-scraper output
so they run in CI without network access or the real CSV file.
"""

import pandas as pd
import pytest
from src.data_collector import clean_text, preprocess_reviews


def _make_raw(**overrides) -> pd.DataFrame:
    """Return a minimal valid raw scraper row as a DataFrame."""
    base = {
        'content': ['Great banking app'],
        'score':   [5],
        'at':      ['2024-03-15 10:00:00'],
        'bank':    ['Commercial Bank of Ethiopia'],
        'source':  ['Google Play'],
    }
    base.update(overrides)
    return pd.DataFrame(base)


# ---------------------------------------------------------------------------
# clean_text
# ---------------------------------------------------------------------------

def test_clean_text_collapses_whitespace():
    assert clean_text("hello   world\t!") == "hello world !"


def test_clean_text_strips_leading_trailing_spaces():
    assert clean_text("  hello  ") == "hello"


def test_clean_text_handles_nan():
    assert clean_text(float('nan')) == ''
    assert clean_text(None) == ''


def test_clean_text_handles_normal_string():
    assert clean_text("normal text") == "normal text"


# ---------------------------------------------------------------------------
# preprocess_reviews — column renaming
# ---------------------------------------------------------------------------

def test_preprocess_renames_columns():
    df = preprocess_reviews(_make_raw())
    assert list(df.columns) == ['review', 'rating', 'date', 'bank', 'source']


# ---------------------------------------------------------------------------
# preprocess_reviews — missing value removal
# ---------------------------------------------------------------------------

def test_preprocess_drops_row_with_missing_review():
    raw = _make_raw(content=[None])
    result = preprocess_reviews(raw)
    assert len(result) == 0


def test_preprocess_drops_row_with_blank_review():
    raw = _make_raw(content=["   "])
    result = preprocess_reviews(raw)
    assert len(result) == 0


def test_preprocess_drops_row_with_missing_rating():
    raw = _make_raw(score=[None])
    result = preprocess_reviews(raw)
    assert len(result) == 0


# ---------------------------------------------------------------------------
# preprocess_reviews — duplicate removal
# ---------------------------------------------------------------------------

def test_preprocess_removes_duplicate_reviews():
    raw = pd.DataFrame({
        'content': ['Great app', 'Great app', 'Different review'],
        'score':   [5, 5, 4],
        'at':      ['2024-01-01'] * 3,
        'bank':    ['CBE', 'CBE', 'CBE'],
        'source':  ['Google Play'] * 3,
    })
    result = preprocess_reviews(raw)
    assert len(result) == 2


def test_preprocess_keeps_same_text_for_different_banks():
    raw = pd.DataFrame({
        'content': ['Good app', 'Good app'],
        'score':   [4, 4],
        'at':      ['2024-01-01'] * 2,
        'bank':    ['CBE', 'BOA'],
        'source':  ['Google Play'] * 2,
    })
    result = preprocess_reviews(raw)
    assert len(result) == 2


# ---------------------------------------------------------------------------
# preprocess_reviews — date normalisation
# ---------------------------------------------------------------------------

def test_preprocess_normalises_date_format():
    raw = _make_raw(at=['2024-03-15 10:30:00'])
    result = preprocess_reviews(raw)
    assert result.iloc[0]['date'] == '2024-03-15'


# ---------------------------------------------------------------------------
# preprocess_reviews — rating range filtering
# ---------------------------------------------------------------------------

def test_preprocess_filters_out_zero_rating():
    raw = _make_raw(score=[0])
    result = preprocess_reviews(raw)
    assert len(result) == 0


def test_preprocess_keeps_valid_ratings_1_to_5():
    raw = pd.DataFrame({
        'content': [f'Review {i}' for i in range(1, 6)],
        'score':   [1, 2, 3, 4, 5],
        'at':      ['2024-01-01'] * 5,
        'bank':    ['CBE'] * 5,
        'source':  ['Google Play'] * 5,
    })
    result = preprocess_reviews(raw)
    assert len(result) == 5
    assert result['rating'].between(1, 5).all()
