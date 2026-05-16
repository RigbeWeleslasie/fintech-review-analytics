-- ============================================================
-- Schema: bank_reviews database
-- Project: fintech-review-analytics
-- Task 3: Database Engineering
-- ============================================================

-- Master table: one row per bank
CREATE TABLE IF NOT EXISTS banks (
    bank_id   SERIAL PRIMARY KEY,
    bank_name VARCHAR(100) NOT NULL UNIQUE,
    app_name  VARCHAR(200)
);

-- Fact table: one row per review
CREATE TABLE IF NOT EXISTS reviews (
    review_id        SERIAL PRIMARY KEY,
    bank_id          INTEGER NOT NULL REFERENCES banks(bank_id) ON DELETE CASCADE,
    review_text      TEXT,
    rating           SMALLINT CHECK (rating BETWEEN 1 AND 5),
    review_date      DATE,
    sentiment_label  VARCHAR(20),
    sentiment_score  NUMERIC(6, 4),
    identified_theme VARCHAR(100),
    source           VARCHAR(50) DEFAULT 'Google Play'
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_reviews_bank_id    ON reviews(bank_id);
CREATE INDEX IF NOT EXISTS idx_reviews_rating     ON reviews(rating);
CREATE INDEX IF NOT EXISTS idx_reviews_date       ON reviews(review_date);
CREATE INDEX IF NOT EXISTS idx_reviews_sentiment  ON reviews(sentiment_label);
CREATE INDEX IF NOT EXISTS idx_reviews_theme      ON reviews(identified_theme);
