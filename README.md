# fintech-review-analytics

**Customer Experience Analytics for Ethiopian Fintech Apps**  
A data engineering pipeline that transforms Google Play Store reviews for three Ethiopian banks into actionable product insights.

---

## Project Overview

This project builds a structured analytics pipeline for Omega Consultancy to advise three Ethiopian banks on improving their mobile banking apps:

| Bank | Google Play App ID | Reviews Collected |
|------|-------------------|-------------------|
| Commercial Bank of Ethiopia (CBE) | `com.combanketh.mobilebanking` | 454 |
| Bank of Abyssinia (BOA) | `com.boa.boaMobileBanking` | 498 |
| Dashen Bank | `com.dashen.dashensuperapp` | 885 |

**Total: 1,837 reviews** — date range: 2022-07-16 to 2026-05-14

---

## Repository Structure

```
fintech-review-analytics/
├── .github/workflows/unittests.yml   # CI/CD — runs pytest on every push
├── .gitignore
├── requirements.txt
├── README.md
├── data/
│   └── raw/                          # gitignored — local only
│       ├── bank_reviews_clean.csv    # 1,837 rows, 5 columns
│       └── bank_reviews_sentiment.csv # 1,837 rows, 8 columns
├── notebooks/
│   ├── data_collection.ipynb         # Task 1: scraping + preprocessing
│   ├── sentiment_analysis.ipynb      # Task 2: sentiment + thematic analysis
│   └── database_setup.ipynb          # Task 3: PostgreSQL schema + insert
├── src/
│   ├── data_collector.py             # Reusable scraping functions
│   └── sentiment_analyzer.py         # Reusable NLP functions
├── scripts/
│   └── preprocess.py                 # Standalone preprocessing CLI script
└── tests/
    └── test_data_collection.py       # Pytest unit tests
```

---

## Environment Setup

**Python version:** 3.11+

```bash
# 1. Clone the repository
git clone https://github.com/RigbeWeleslasie/fintech-review-analytics.git
cd fintech-review-analytics

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # Linux/Mac
# venv\Scripts\activate           # Windows

# 3. Install all dependencies
pip install -r requirements.txt
```

---

## Running the Pipeline

### Task 1 — Data Collection & Preprocessing

```bash
# Option A: run the notebook interactively
jupyter notebook notebooks/data_collection.ipynb

# Option B: run the standalone script (CLI)
python scripts/preprocess.py
```

Outputs: `data/raw/bank_reviews_clean.csv` (columns: `review, rating, date, bank, source`)

### Task 2 — Sentiment & Thematic Analysis

```bash
jupyter notebook notebooks/sentiment_analysis.ipynb
```

Outputs: `data/raw/bank_reviews_sentiment.csv` (adds `sentiment_score, sentiment_label, identified_theme`)

### Task 3 — PostgreSQL Database

```bash
# Requires PostgreSQL running locally (see Database Setup below)
jupyter notebook notebooks/database_setup.ipynb
```

### Running Unit Tests

```bash
pytest tests/ -v
```

---

## Scraping Methodology

Reviews were scraped using the [`google-play-scraper`](https://pypi.org/project/google-play-scraper/) Python library.

**Parameters used:**
- Language: `en` (English), Country: `et` (Ethiopia)
- Sort: `Sort.NEWEST` to capture the most recent feedback
- Target count: 500–600 per bank

**Limitations encountered:**
- The original Dashen Bank app ID (`com.dashen.dashensmart`) returned zero results — the app migrated to `com.dashen.dashensuperapp` (Dashen Super App). The updated ID was used.
- BOA returned 498 reviews (below the 500 target) due to Google Play rate limiting at the time of scraping. The minimum threshold of 400 is met.
- Only English-language reviews were collected; Amharic reviews were excluded from this iteration (a significant limitation given the user base).

---

## Data Quality Summary

| Metric | Value |
|--------|-------|
| Total reviews collected | 1,837 |
| Duplicate reviews removed | 0 (none found) |
| Reviews missing `review` text | 0 |
| Reviews missing `rating` | 0 |
| Missing data rate | **< 1%** |
| Date format | Normalised to `YYYY-MM-DD` |

---

## Sentiment Analysis Summary (Task 2)

**Tool:** VADER (Valence Aware Dictionary and sEntiment Reasoner)  
**Rationale:** Designed for short social-media text; handles punctuation, capitalisation, and emojis; no GPU required; interpretable compound score [-1, +1].

| Bank | Positive | Neutral | Negative | Avg Rating |
|------|----------|---------|----------|------------|
| CBE | 56.6% | 30.0% | 13.4% | 3.93 ★ |
| BOA | 43.4% | 34.9% | 21.7% | 3.29 ★ |
| Dashen | 57.9% | 27.5% | 14.7% | 3.86 ★ |

**Themes identified per bank:** Transaction Performance, App Stability & Technical Issues, User Experience & Design, Account & Security, Customer Support, General Feedback.

---

## Database Setup (Task 3)

**Prerequisites:** PostgreSQL 14+ installed and running locally.

```bash
# Create the database and user
sudo -u postgres psql -c "CREATE DATABASE bank_reviews;"
sudo -u postgres psql -c "CREATE USER bankuser WITH PASSWORD 'bankpass123';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE bank_reviews TO bankuser;"
```

Schema is documented in `notebooks/database_setup.ipynb`.

---

## CI/CD

GitHub Actions workflow (`.github/workflows/unittests.yml`) runs on every push to any branch:
1. Installs dependencies from `requirements.txt`
2. Runs `pytest tests/ -v`

---

## Ethical Considerations

- **Negativity bias:** Users are more likely to leave a review after a frustrating experience, so negative percentages likely overstate dissatisfaction among the full user base.
- **Sampling bias:** Only English-language reviews were scraped. Given that most Ethiopian bank users communicate in Amharic, the dataset under-represents the majority of users.
- **Date skew:** `Sort.NEWEST` means older experiences are under-represented.

---

## Dependencies

See [requirements.txt](requirements.txt) for the full list. Key packages:

- `google-play-scraper` — review scraping
- `pandas`, `numpy` — data manipulation
- `vaderSentiment` — sentiment scoring
- `scikit-learn` — TF-IDF keyword extraction
- `transformers` — optional DistilBERT pipeline
- `psycopg2-binary`, `sqlalchemy` — PostgreSQL integration
- `matplotlib`, `seaborn` — visualisation
- `pytest` — unit testing
