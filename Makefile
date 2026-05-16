.PHONY: setup test lint scrape help

help:
	@echo "Available targets:"
	@echo "  make setup   — create venv and install dependencies"
	@echo "  make test    — run all unit tests"
	@echo "  make lint    — check code style with flake8"
	@echo "  make scrape  — scrape and preprocess reviews (writes data/raw/bank_reviews_clean.csv)"

setup:
	python -m venv venv
	venv/bin/pip install --upgrade pip
	venv/bin/pip install -r requirements.txt

test:
	pytest tests/ -v

lint:
	flake8 src/ scripts/ tests/ --max-line-length 100 --exclude venv

scrape:
	python scripts/preprocess.py --count 500 --output data/raw/bank_reviews_clean.csv
