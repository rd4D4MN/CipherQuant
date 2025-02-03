-- Remove entries with NULL prices (these are likely invalid)
DELETE FROM prices 
WHERE close_price IS NULL 
   OR open_price IS NULL 
   OR high_price IS NULL 
   OR low_price IS NULL;
-- Log the number of rows affected
DO $$ 
DECLARE
    rows_deleted INTEGER;
BEGIN
    GET DIAGNOSTICS rows_deleted = ROW_COUNT;
    RAISE NOTICE 'Deleted % rows with NULL prices', rows_deleted;
END $$;

-- Remove future dates
DELETE FROM prices 
WHERE price_date > CURRENT_DATE;
-- Log the number of rows affected
DO $$ 
DECLARE
    rows_deleted INTEGER;
BEGIN
    GET DIAGNOSTICS rows_deleted = ROW_COUNT;
    RAISE NOTICE 'Deleted % rows with future dates', rows_deleted;
END $$;

-- Remove entries with zero volume (likely invalid market data)
DELETE FROM prices 
WHERE volume = 0 OR volume IS NULL;
-- Log the number of rows affected
DO $$ 
DECLARE
    rows_deleted INTEGER;
BEGIN
    GET DIAGNOSTICS rows_deleted = ROW_COUNT;
    RAISE NOTICE 'Deleted % rows with zero volume', rows_deleted;
END $$;

-- Analyze the table for better query performance
ANALYZE prices;
