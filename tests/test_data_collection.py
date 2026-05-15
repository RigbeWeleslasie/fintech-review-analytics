import pytest
import pandas as pd
import os

def test_csv_exists():
    assert os.path.exists('data/raw/bank_reviews_clean.csv')

def test_csv_columns():
    df = pd.read_csv('data/raw/bank_reviews_clean.csv')
    required = ['review', 'rating', 'date', 'bank', 'source']
    for col in required:
        assert col in df.columns, f"Missing column: {col}"

def test_min_reviews():
    df = pd.read_csv('data/raw/bank_reviews_clean.csv')
    for bank in df['bank'].unique():
        count = len(df[df['bank'] == bank])
        assert count >= 400, f"{bank} has only {count} reviews"

def test_rating_range():
    df = pd.read_csv('data/raw/bank_reviews_clean.csv')
    assert df['rating'].between(1, 5).all()

def test_no_missing_values():
    df = pd.read_csv('data/raw/bank_reviews_clean.csv')
    assert df[['review','rating','date','bank','source']].isnull().sum().sum() == 0

def test_three_banks():
    df = pd.read_csv('data/raw/bank_reviews_clean.csv')
    assert len(df['bank'].unique()) == 3
