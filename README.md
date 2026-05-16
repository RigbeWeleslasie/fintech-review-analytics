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
├── .github/workflows/unittests.yml      # CI/CD — runs pytest on every push
├── .gitignore
├── requirements.txt
├── Makefile                             # make setup / test / lint / scrape
├── CONTRIBUTING.md                      # setup, conventions, branch strategy
├── README.md
├── data/                                # CSV files gitignored — see data/README.md
│   ├── README.md                        # documents data flow and how to reproduce
│   └── raw/
│       ├── bank_reviews_clean.csv       # produced by scripts/preprocess.py (Task 1)
│       └── bank_reviews_sentiment.csv   # produced by sentiment_analysis.ipynb (Task 2)
├── notebooks/
│   ├── data_collection.ipynb            # Task 1: scraping + preprocessing
│   ├── sentiment_analysis.ipynb         # Task 2: sentiment + thematic analysis
│   ├── database_setup.ipynb             # Task 3: PostgreSQL schema + insert
│   └── insights_recommendations.ipynb  # Task 4: insights + visualisations
├── src/
│   ├── data_collector.py                # Reusable scraping and preprocessing functions
│   └── sentiment_analyzer.py            # Reusable VADER, TF-IDF, and theme functions
├── scripts/
│   ├── preprocess.py                    # Standalone scrape + preprocess CLI
│   └── schema.sql                       # PostgreSQL DDL for bank_reviews database
└── tests/
    ├── conftest.py                      # Session fixture: generates sample CSV for CI
    ├── test_data_collection.py          # CSV schema and data quality checks
    ├── test_preprocessing.py            # Unit tests for clean_text and preprocess_reviews
    └── test_sentiment_analyzer.py       # Unit tests for VADER, themes, TF-IDF, pipeline
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

Reviews were scraped using the [`google-play-scraper`](https://pypi.org/project/google-play-scraper/) Python library on **14 May 2026**.

### Bank identifiers

| Bank | App ID(s) | Notes |
|------|-----------|-------|
| Commercial Bank of Ethiopia | `com.combanketh.mobilebanking` | Single active app |
| Bank of Abyssinia | `com.boa.boaMobileBanking` | Single active app |
| Dashen Bank | `com.dashen.dashensuperapp` (primary)<br>`com.cr2.amolelight` (legacy) | Dashen migrated from the legacy Amole app to a super-app; both IDs are scraped and combined so historical reviews are not lost |

### Scraping parameters

| Parameter | Value | Reason |
|-----------|-------|--------|
| `lang` | `en` | English-language reviews only |
| `country` | `et` | Ethiopia store |
| `sort` | `Sort.NEWEST` | Prioritises recent feedback over most-liked |
| `count` | 500 per app ID | Upper bound; actual yield depends on available reviews |
| Sleep between requests | 1 second | Polite rate-limiting to avoid Play Store throttling |

To reproduce with different parameters:
```bash
python scripts/preprocess.py --count 500 --lang en --country et --output data/raw/bank_reviews_clean.csv
```

### Date range of collected reviews

Reviews span **2022-07-16 to 2026-05-14** (sorted newest-first, cutoff by available review count).

### Rate-limit and localization constraints

- **Rate limiting:** Google Play's unofficial API does not publish rate limits. A 1-second sleep between requests (`time.sleep(1)`) was sufficient for this dataset size. For counts above 1,000 per app, increase the sleep to 2–3 seconds to avoid `HTTP 429` errors.
- **Language filter:** Only `lang='en'` reviews are returned. A significant portion of Ethiopian bank users write in Amharic; those reviews are excluded. This means negative sentiment is likely under-reported for CBE and BOA whose user bases skew toward Amharic speakers.
- **Country filter:** `country='et'` restricts results to the Ethiopian Play Store. Reviews from diaspora users on other country stores are not captured.
- **Review availability:** BOA returned 498 reviews (below the 500 target) — the Play Store had fewer English reviews available. Minimum threshold of 400 per bank is met for all three banks.

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
