# Notebooks

This directory contains the Jupyter notebooks for each task of the fintech-review-analytics pipeline.

---

## Notebooks Overview

| Notebook | Task | Description |
|----------|------|-------------|
| [data_collection.ipynb](data_collection.ipynb) | Task 1 | Scrapes Google Play reviews for CBE, BOA, and Dashen Bank using `google-play-scraper`, cleans and preprocesses the data, and saves a 5-column CSV |
| [sentiment_analysis.ipynb](sentiment_analysis.ipynb) | Task 2 | Applies VADER sentiment scoring, extracts top keywords with TF-IDF, assigns business themes, and produces visualisations of sentiment and theme distributions |
| [database_setup.ipynb](database_setup.ipynb) | Task 3 | Creates the `bank_reviews` PostgreSQL schema (`banks` + `reviews` tables), inserts all processed review data, and runs verification queries |

---

## How to Run

```bash
# From the project root, activate the virtual environment first
source venv/bin/activate

# Launch Jupyter
jupyter notebook
```

Then open each notebook in the order listed above. Each notebook sets `os.chdir` to the project root, so it can be run from any working directory.

**Run order:**
1. `data_collection.ipynb` → produces `data/raw/bank_reviews_clean.csv`
2. `sentiment_analysis.ipynb` → produces `data/raw/bank_reviews_sentiment.csv`
3. `database_setup.ipynb` → populates PostgreSQL `bank_reviews` database

---

## Output Files

All output files are gitignored (`data/` is excluded). After running the notebooks locally you will find:

| File | Produced by | Columns |
|------|-------------|---------|
| `data/raw/bank_reviews_clean.csv` | `data_collection.ipynb` | `review, rating, date, bank, source` |
| `data/raw/bank_reviews_sentiment.csv` | `sentiment_analysis.ipynb` | above + `sentiment_score, sentiment_label, identified_theme` |

---

## Visualisations

The following plots are saved to this directory by `sentiment_analysis.ipynb`:

| File | Description |
|------|-------------|
| `sentiment_by_bank.png` | Stacked bar chart of sentiment distribution (%) and average star rating per bank |
| `rating_distribution.png` | Line chart of rating frequency (1–5 stars) per bank |
| `theme_distribution.png` | Grouped and normalised bar charts of theme frequency per bank |
