-- Optional: Drop tables if they exist (for development / testing)
DROP TABLE IF EXISTS prices;
DROP TABLE IF EXISTS volumes;
DROP TABLE IF EXISTS vc_investors;

-- 1) Prices Table
--    Stores daily price data for various assets (e.g., crypto symbols).
CREATE TABLE prices (
    id SERIAL PRIMARY KEY,           -- if using Postgres; use INTEGER PRIMARY KEY AUTOINCREMENT for SQLite
    symbol VARCHAR(10) NOT NULL,
    price_date DATE NOT NULL,
    price DECIMAL(18, 2) NOT NULL
);

-- 2) Volumes Table
--    Stores trading volume data for assets on a daily basis.
CREATE TABLE volumes (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    volume_date DATE NOT NULL,
    volume BIGINT NOT NULL
);

-- 3) VC Investors Table
--    Tracks various Venture Capital (VC) investors and (example) their portfolio info.
CREATE TABLE vc_investors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    portfolio_size INT DEFAULT 0,
    last_investment_date DATE
);

-- Optionally, you can create indexes for faster lookups if needed:
CREATE INDEX idx_prices_symbol ON prices(symbol);
CREATE INDEX idx_volumes_symbol ON volumes(symbol);
CREATE INDEX idx_investors_name ON vc_investors(name);
