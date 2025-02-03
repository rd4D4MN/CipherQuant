-- Check total number of entries per symbol
SELECT 
    symbol,
    COUNT(*) as total_records,
    MIN(price_date) as earliest_date,
    MAX(price_date) as latest_date,
    COUNT(*) * 100.0 / (SELECT COUNT(*) FROM prices) as percentage
FROM prices
GROUP BY symbol
ORDER BY total_records DESC;

-- Check for missing dates in the last 30 days
WITH RECURSIVE date_series AS (
    SELECT CURRENT_DATE - INTERVAL '30 days' as date
    UNION ALL
    SELECT date + INTERVAL '1 day'
    FROM date_series
    WHERE date < CURRENT_DATE
),
missing_dates AS (
    SELECT 
        d.date,
        p.symbol,
        p.close_price
    FROM date_series d
    CROSS JOIN (SELECT DISTINCT symbol FROM prices) s
    LEFT JOIN prices p ON d.date = p.price_date AND s.symbol = p.symbol
    WHERE d.date <= CURRENT_DATE
        AND d.date >= CURRENT_DATE - INTERVAL '30 days'
        AND EXTRACT(DOW FROM d.date) NOT IN (0, 6) -- Exclude weekends
)
SELECT 
    symbol,
    COUNT(*) FILTER (WHERE close_price IS NULL) as missing_days,
    STRING_AGG(
        CASE WHEN close_price IS NULL THEN date::text ELSE NULL END,
        ', '
    ) as missing_dates
FROM missing_dates
GROUP BY symbol
HAVING COUNT(*) FILTER (WHERE close_price IS NULL) > 0;

-- Check for null values in important columns
SELECT 
    symbol,
    COUNT(*) FILTER (WHERE open_price IS NULL) as null_open,
    COUNT(*) FILTER (WHERE high_price IS NULL) as null_high,
    COUNT(*) FILTER (WHERE low_price IS NULL) as null_low,
    COUNT(*) FILTER (WHERE close_price IS NULL) as null_close,
    COUNT(*) FILTER (WHERE volume IS NULL) as null_volume,
    COUNT(*) as total_records
FROM prices
GROUP BY symbol
HAVING COUNT(*) FILTER (WHERE open_price IS NULL) > 0
    OR COUNT(*) FILTER (WHERE high_price IS NULL) > 0
    OR COUNT(*) FILTER (WHERE low_price IS NULL) > 0
    OR COUNT(*) FILTER (WHERE close_price IS NULL) > 0
    OR COUNT(*) FILTER (WHERE volume IS NULL) > 0;

-- Show the most recent entries
SELECT 
    symbol,
    price_date,
    open_price,
    high_price,
    low_price,
    close_price,
    volume
FROM prices
WHERE price_date >= CURRENT_DATE - INTERVAL '5 days'
ORDER BY symbol, price_date DESC;
