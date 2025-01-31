WITH price_volume_data AS (
    SELECT
        p.symbol,
        p.price_date AS date,
        p.price,
        v.volume
    FROM prices p
    JOIN volumes v
        ON p.symbol = v.symbol
        AND p.price_date = v.volume_date
)
SELECT
    corr(price, volume) AS price_volume_corr
FROM price_volume_data;