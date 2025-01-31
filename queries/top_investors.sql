SELECT
    name,
    portfolio_size
FROM vc_investors
ORDER BY portfolio_size DESC
LIMIT 10;