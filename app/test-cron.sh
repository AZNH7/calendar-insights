#!/bin/bash

# Set up logging
LOG_DIR="/var/log/app"
mkdir -p $LOG_DIR
exec 1> >(tee -a "${LOG_DIR}/test-cron.log") 2>&1

echo "=== Starting Cron Job Test at $(date) ==="

# Print environment
echo "Working Directory: $(pwd)"
echo "Python Version: $(/usr/local/bin/python --version)"

# Change to app directory
cd /app

# Cron test
echo "Running cron job test..."
### TODO ###

# Check the database
echo "Database status:"

postsql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB} -c "SELECT * FROM test_table;"
if [ $? -ne 0 ]; then
    echo "Database connection failed!"
    exit 1
fi
echo "Database connection successful!"
echo "Running database query..."
psql postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB} -c "SELECT * FROM test_table;"
if [ $? -ne 0 ]; then
    echo "Database query failed!"
    exit 1
fi
echo "Database query successful!"
echo "Running database cleanup..."
psql postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB} -c "DELETE FROM test_table WHERE condition;"
if [ $? -ne 0 ]; then
    echo "Database cleanup failed!"
    exit 1
fi
echo "Database cleanup successful!"

echo "=== Cron Job Test Complete at $(date) ===" 