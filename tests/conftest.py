import pytest
import pandas as pd
import os

@pytest.fixture(scope="session", autouse=True)
def create_sample_csv():
    """Create a minimal sample CSV for CI where the real data file is gitignored."""
    path = "data/raw/bank_reviews_clean.csv"
    if os.path.exists(path):
        return  # real file exists locally — use it

    os.makedirs("data/raw", exist_ok=True)
    sample = []
    banks = [
        "Commercial Bank of Ethiopia",
        "Bank of Abyssinia",
        "Dashen Bank",
    ]
    for bank in banks:
        for i in range(400):
            sample.append({
                "review":  f"Sample review {i} for {bank}",
                "rating":  (i % 5) + 1,
                "date":    "2024-01-01",
                "bank":    bank,
                "source":  "Google Play",
            })

    pd.DataFrame(sample).to_csv(path, index=False)
