# Contributing

## Setup

```bash
git clone https://github.com/RigbeWeleslasie/fintech-review-analytics.git
cd fintech-review-analytics
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your PostgreSQL credentials
```

## Running the full pipeline in one command

```bash
# 1. Scrape and preprocess reviews
python scripts/preprocess.py --count 500 --output data/raw/bank_reviews_clean.csv

# 2. Run sentiment + thematic analysis (from repo root)
jupyter nbconvert --to notebook --execute notebooks/sentiment_analysis.ipynb

# 3. Load into PostgreSQL
jupyter nbconvert --to notebook --execute notebooks/database_setup.ipynb
```

Or use the Makefile shortcuts:

```bash
make setup    # create venv and install dependencies
make test     # run all 42 tests
make lint     # check style with flake8
make scrape   # run scripts/preprocess.py with default settings
```

## Running tests

```bash
pytest tests/ -v
```

Tests are split into three files:
- `tests/test_data_collection.py` — CSV schema and data quality checks
- `tests/test_preprocessing.py` — unit tests for `clean_text` and `preprocess_reviews`
- `tests/test_sentiment_analyzer.py` — unit tests for VADER scoring, theme assignment, TF-IDF

All tests run without network access or the real CSV file (CI generates synthetic data via `conftest.py`).

## Branch strategy

| Branch | Purpose |
|--------|---------|
| `main` | Stable, reviewed code only — merge via PR |
| `task-1` | Data collection and preprocessing |
| `task-2` | Sentiment and thematic analysis |
| `task-3` | Database schema and insertion |
| `task-4` | Insights and recommendations |

## Coding conventions

- **Formatter:** `black` — run `black src/ scripts/ tests/` before committing
- **Linter:** `flake8 --max-line-length 100`
- **Types:** use type hints on all public functions
- **Logging:** use `logging.getLogger(__name__)` in modules; `print()` only in notebooks
- **Secrets:** never hardcode credentials — load from `.env` via `python-dotenv`
- **Comments:** explain *why*, not *what* — skip obvious restatements of the code
- **Tests:** add at least one test for any new public function in `src/`

## Commit message format

```
<type>: <short description>

type = feat | fix | test | docs | chore | refactor
```

Example: `feat: add TF-IDF keyword extraction to sentiment pipeline`
