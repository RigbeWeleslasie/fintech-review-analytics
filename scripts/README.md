# Scripts

Standalone scripts and SQL files for the fintech-review-analytics pipeline.
These can be run independently from the command line without launching Jupyter.

---

## Files

| File | Task | Description |
|------|------|-------------|
| [preprocess.py](preprocess.py) | Task 1 | Scrapes Google Play reviews for all three banks and saves a clean 5-column CSV to `data/raw/bank_reviews_clean.csv` |
| [schema.sql](schema.sql) | Task 3 | PostgreSQL DDL — creates the `banks` and `reviews` tables with indexes |

---

## Usage

### `preprocess.py` — Scrape & Clean Reviews

```bash
# From the project root with the virtual environment active
source venv/bin/activate
python scripts/preprocess.py
```

**What it does:**
1. Scrapes up to 500 reviews per bank from the Google Play Store
2. Renames columns to the standard format: `review, rating, date, bank, source`
3. Drops rows missing review text or rating
4. Removes duplicate reviews
5. Normalises dates to `YYYY-MM-DD`
6. Saves the result to `data/raw/bank_reviews_clean.csv`
7. Prints a data quality report (counts, missing values, per-bank totals)

**Output:** `data/raw/bank_reviews_clean.csv`

---

### `schema.sql` — PostgreSQL Schema

Apply the schema to an existing database:

```bash
psql -U bankuser -d bank_reviews -f scripts/schema.sql
```

Or from inside `psql`:

```sql
\i scripts/schema.sql
```

**Tables created:**
- `banks(bank_id, bank_name, app_name)` — master table, one row per bank
- `reviews(review_id, bank_id, review_text, rating, review_date, sentiment_label, sentiment_score, identified_theme, source)` — fact table

See [notebooks/database_setup.ipynb](../notebooks/database_setup.ipynb) for the full data insertion workflow.

---

## Database Setup (prerequisite for schema.sql)

```bash
sudo -u postgres psql -p 5433 -c "CREATE DATABASE bank_reviews;"
sudo -u postgres psql -p 5433 -c "CREATE USER bankuser WITH PASSWORD 'bankpass123';"
sudo -u postgres psql -p 5433 -c "GRANT ALL PRIVILEGES ON DATABASE bank_reviews TO bankuser;"
```

Copy `.env.example` to `.env` and fill in your credentials before running the notebooks.
