#!/bin/bash
set -e

# Print current working directory and contents
echo "Current working directory: $(pwd)"
echo "Contents of current directory: $(ls -la)"

# Wait for PostgreSQL
echo "Waiting for PostgreSQL to be ready..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q'; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is up - executing database initialization"

# Initialize database
echo "Initializing PostgreSQL database..."
python init_db.py

# Verify database initialization
echo "Verifying database initialization..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\d meetings'

# Set up logging directory with proper permissions
mkdir -p /var/log/app
chown -R appuser:appuser /var/log/app
chmod 755 /var/log/app

# Install cron
apt-get update && apt-get install -y cron

# Cron logging
touch /var/log/app/cron.log
touch /var/log/app/test-cron.log
chown appuser:appuser /var/log/app/cron.log
chown appuser:appuser /var/log/app/test-cron.log

# Make test-cron.sh executable
chmod +x /app/test-cron.sh

# Install crontab
crontab /app/crontab

# Start cron service
service cron start

# Monitor logs in background
tail -f /var/log/app/cron.log &
tail -f /var/log/app/test-cron.log &

# Start Streamlit
echo "Starting Streamlit..."
exec streamlit run --server.address 0.0.0.0 --server.port 8501 dashboard.py