# Load environment variables from .env file
export $(grep -v '^#' $(git rev-parse --show-toplevel)/.env | xargs)

# Ensure PostgreSQL is running
echo "Checking if PostgreSQL is running..."
pg_isready -h $DB_HOST -p $DB_PORT

# Drop and recreate the database
echo "Resetting the database..."
PGPASSWORD=$DB_PASSWORD dropdb -U $DB_USER --if-exists $DB_NAME
PGPASSWORD=$DB_PASSWORD createdb -U $DB_USER $DB_NAME

# Run schema
echo "Running schema..."
PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d $DB_NAME -f db/schema.sql

# Insert test data
echo "Inserting test data..."
PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d $DB_NAME -c "INSERT INTO prices (symbol, price_date, price) VALUES ('BTC', '2024-01-01', 45000.00);"
PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d $DB_NAME -c "INSERT INTO volumes (symbol, volume_date, volume) VALUES ('BTC', '2024-01-01', 1200000);"
PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d $DB_NAME -c "INSERT INTO vc_investors (name, portfolio_size) VALUES ('Alpha Ventures', 100);"

# Run queries
echo "Running queries..."
PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d $DB_NAME -f queries/top_investors.sql
PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d $DB_NAME -f queries/correlation_analysis.sql

echo "Database setup complete!"
