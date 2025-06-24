#!/bin/bash

# Enhanced Calendar Insights Deployment with Dynamic Data Fetching Options
# This script deploys the calendar insights service with flexible data fetching options

set -e

# Environment variables with validation
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-${GCP_PROJECT_ID}}"
REGION="${GCP_REGION:-europe-west3}"
SERVICE_NAME="${CLOUD_RUN_SERVICE_NAME:-calendar-insights}"
REPOSITORY_NAME="${ARTIFACT_REGISTRY_REPO:-calendar-insights-repo}"
DB_INSTANCE_NAME="${CLOUD_SQL_INSTANCE_NAME:-calendar-insights-db}"

# Validate required environment variables
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: GOOGLE_CLOUD_PROJECT or GCP_PROJECT_ID environment variable must be set"
    exit 1
fi

IMAGE_NAME="${GCP_REGION:-europe-west3}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY_NAME}/${SERVICE_NAME}"

echo "🚀 Enhanced Calendar Insights Deployment"
echo "=========================================="
echo "📋 Configuration:"
echo "   Project ID: ${PROJECT_ID}"
echo "   Region: ${REGION}"
echo "   Service Name: ${SERVICE_NAME}"
echo "   DB Instance: ${DB_INSTANCE_NAME}"
echo ""

# Function to show options
show_data_options() {
    echo ""
    echo "📊 CALENDAR DATA FETCHING OPTIONS:"
    echo "1. Fresh start (no historical data) - Only daily incremental updates"
    echo "2. Fetch 1 year of historical data + daily updates"
    echo "3. Fetch 2 years of historical data + daily updates"
    echo "4. Fetch 3 years of historical data + daily updates"
    echo "5. Fetch 5 years of historical data + daily updates"
    echo "6. Custom number of years"
    echo "7. Skip data fetching for now (deploy infrastructure only)"
    echo ""
}

# Get user choice for data fetching
get_data_choice() {
    show_data_options
    while true; do
        read -p "Choose an option (1-7): " choice
        case $choice in
            1) YEARS=0; break;;
            2) YEARS=1; break;;
            3) YEARS=2; break;;
            4) YEARS=3; break;;
            5) YEARS=5; break;;
            6) 
                read -p "Enter number of years (1-10): " custom_years
                if [[ $custom_years =~ ^[1-9]$|^10$ ]]; then
                    YEARS=$custom_years
                    break
                else
                    echo "❌ Please enter a number between 1 and 10"
                fi
                ;;
            7) YEARS=-1; break;;
            *) echo "❌ Please choose a valid option (1-7)";;
        esac
    done
}

# Build and push Docker image
echo "🏗️  Building Docker image..."
docker build -t $IMAGE_NAME .
docker push $IMAGE_NAME

# Deploy Cloud Run service
echo "🚀 Deploying Cloud Run service..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 900 \
    --set-env-vars "POSTGRES_HOST=/cloudsql/${PROJECT_ID}:${REGION}:${DB_INSTANCE_NAME},POSTGRES_PORT=5432,ENVIRONMENT=production" \
    --set-secrets "POSTGRES_DB=postgres_db:latest,POSTGRES_USER=postgres_user:latest,POSTGRES_PASSWORD=postgres_password:latest" \
    --set-cloudsql-instances ${PROJECT_ID}:${REGION}:${DB_INSTANCE_NAME}

# Update database schema
echo "🔧 Updating database schema..."
gcloud run jobs create schema-update-job \
    --image $IMAGE_NAME \
    --region $REGION \
    --set-env-vars "POSTGRES_HOST=/cloudsql/${PROJECT_ID}:${REGION}:${DB_INSTANCE_NAME},POSTGRES_PORT=5432,ENVIRONMENT=production" \
    --set-secrets "POSTGRES_DB=postgres_db:latest,POSTGRES_USER=postgres_user:latest,POSTGRES_PASSWORD=postgres_password:latest" \
    --set-cloudsql-instances ${PROJECT_ID}:${REGION}:${DB_INSTANCE_NAME} \
    --command python3 \
    --args "update_schema.py" \
    --task-timeout 300 \
    2>/dev/null || echo "Schema update job already exists"

gcloud run jobs execute schema-update-job --region $REGION --wait

# Create/update dynamic fetch job
echo "🔄 Setting up dynamic data fetching job..."
gcloud run jobs create dynamic-fetch-job \
    --image $IMAGE_NAME \
    --region $REGION \
    --set-env-vars "POSTGRES_HOST=/cloudsql/${PROJECT_ID}:${REGION}:${DB_INSTANCE_NAME},POSTGRES_PORT=5432,ENVIRONMENT=production" \
    --set-secrets "POSTGRES_DB=postgres_db:latest,POSTGRES_USER=postgres_user:latest,POSTGRES_PASSWORD=postgres_password:latest" \
    --set-cloudsql-instances ${PROJECT_ID}:${REGION}:${DB_INSTANCE_NAME} \
    --command python3 \
    --args "dynamic_fetch.py" \
    --task-timeout 1800 \
    --memory 2Gi \
    --cpu 2 \
    2>/dev/null || echo "Dynamic fetch job already exists"

# Get user's data preference
get_data_choice

# Handle data fetching based on user choice
if [ $YEARS -eq -1 ]; then
    echo "⏭️  Skipping data fetching. Infrastructure deployed successfully!"
    echo ""
    echo "📝 To fetch data later, use these commands:"
    echo "   Historical (3 years): gcloud run jobs execute dynamic-fetch-job --region $REGION --args='--years 3'"
    echo "   Daily update: gcloud run jobs execute dynamic-fetch-job --region $REGION --args='--daily'"
    
elif [ $YEARS -eq 0 ]; then
    echo "🔄 Setting up for incremental-only fetching (no historical data)..."
    echo "📊 This option starts fresh with only daily updates going forward."
    
else
    echo "📚 Fetching $YEARS year(s) of historical calendar data..."
    echo "⏱️  This may take several minutes depending on your calendar history..."
    
    # Execute historical data fetch
    gcloud run jobs execute dynamic-fetch-job \
        --region $REGION \
        --args="--years $YEARS" \
        --wait
fi

# Set up daily cron job
echo "⏰ Setting up daily cron job..."
gcloud scheduler jobs create http daily-calendar-fetch \
    --schedule="0 2 * * *" \
    --uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/dynamic-fetch-job:run" \
    --http-method=POST \
    --oauth-service-account-email="${SERVICE_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --headers="Content-Type=application/json" \
    --message-body='{"spec":{"template":{"spec":{"template":{"spec":{"containers":[{"args":["dynamic_fetch.py","--daily"]}]}}}}}}' \
    --location=$REGION \
    --time-zone="Europe/Berlin" \
    2>/dev/null || echo "Daily cron job already exists"

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo ""
echo "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!"
echo "======================================="
echo ""
echo "📊 Dashboard URL: $SERVICE_URL"
echo ""
echo "🔧 MANAGEMENT COMMANDS:"
echo "  Fetch historical data: gcloud run jobs execute dynamic-fetch-job --region $REGION --args='--years X'"
echo "  Daily update:          gcloud run jobs execute dynamic-fetch-job --region $REGION --args='--daily'"
echo "  Last 30 days:          gcloud run jobs execute dynamic-fetch-job --region $REGION --args='--days 30'"
echo ""
echo "⏰ AUTOMATED SCHEDULE:"
echo "  - Daily fetch at 2:00 AM (Europe/Berlin time)"
echo "  - View jobs: gcloud scheduler jobs list --location=$REGION"
echo ""
echo "📈 DATA STATUS:"
if [ $YEARS -gt 0 ]; then
    echo "  - Historical data: $YEARS year(s) fetched"
elif [ $YEARS -eq 0 ]; then
    echo "  - Historical data: None (fresh start)"
else
    echo "  - Historical data: Not fetched yet"
fi
echo "  - Daily updates: Enabled (2:00 AM daily)"
echo ""
echo "🔄 To modify the daily schedule:"
echo "  gcloud scheduler jobs update http daily-calendar-fetch --schedule='0 3 * * *' --location=$REGION"
echo ""

# Test the deployment
echo "🧪 Testing deployment..."
echo "Checking service health..."
if curl -s --max-time 30 "$SERVICE_URL" > /dev/null; then
    echo "✅ Service is responding successfully!"
else
    echo "⚠️  Service might still be starting up. Please wait a moment and try accessing the dashboard."
fi

echo ""
echo "✨ Your Calendar Insights service is ready!" 