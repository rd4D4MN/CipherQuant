-- Remove entries with NULL prices (these are likely invalid)
DELETE FROM prices 
WHERE close_price IS NULL 
   OR open_price IS NULL 
   OR high_price IS NULL 
   OR low_price IS NULL;

-- Remove future dates
DELETE FROM prices 
WHERE price_date > CURRENT_DATE;

-- Remove entries with zero volume (likely invalid market data)
DELETE FROM prices 
WHERE volume = 0 OR volume IS NULL;

-- Analyze the table for better query performance
ANALYZE prices;
