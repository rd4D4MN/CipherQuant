-- Drop tables if they exist (for development/testing)
DROP TABLE IF EXISTS prices;
DROP TABLE IF EXISTS volumes;

-- Prices Table: Stores daily OHLCV data for assets
CREATE TABLE prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    price_date DATE NOT NULL,
    open_price DECIMAL(18,2),
    high_price DECIMAL(18,2),
    low_price DECIMAL(18,2),
    close_price DECIMAL(18,2),
    volume BIGINT,
    market_source VARCHAR(20) DEFAULT 'stock', -- 'stock' or 'crypto'
    UNIQUE(symbol, price_date) -- Prevents duplicate entries
);

-- Indexes for performance
CREATE INDEX idx_prices_symbol_date ON prices(symbol, price_date);
CREATE INDEX idx_prices_date ON prices(price_date);
