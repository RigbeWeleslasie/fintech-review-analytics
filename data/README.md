# Data Directory

All data files are **gitignored** and must be generated locally by running the pipeline.
This directory is committed only to document the expected structure.

```
data/
└── raw/
    ├── bank_reviews_clean.csv       # produced by scripts/preprocess.py (Task 1)
    │                                # columns: review, rating, date, bank, source
    │                                # ~1,837 rows after deduplication
    │
    └── bank_reviews_sentiment.csv   # produced by notebooks/sentiment_analysis.ipynb (Task 2)
                                     # adds: review_id, review_text, sentiment_score,
                                     #        sentiment_label, identified_theme
```

## Reproducing the data

```bash
# Step 1 — scrape and preprocess (requires internet access)
python scripts/preprocess.py --count 500 --output data/raw/bank_reviews_clean.csv

# Step 2 — sentiment and thematic analysis
jupyter nbconvert --to notebook --execute notebooks/sentiment_analysis.ipynb --inplace

# Step 3 — load into PostgreSQL (requires local DB, see README.md)
jupyter nbconvert --to notebook --execute notebooks/database_setup.ipynb --inplace
```

## Why data files are not committed

- CSV files can be large and change every time the scraper runs (Play Store reviews update continuously).
- Committing raw data would expose user-generated content of uncertain licensing.
- The pipeline is fully reproducible from the committed scripts and notebooks.
