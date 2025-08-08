#!/bin/bash

# Demo Calendar Insights Deployment
# This script deploys a demo version of the calendar insights service
# It's designed to be lightweight and suitable for demonstration purposes

set -e

# Environment variables with validation
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-${GCP_PROJECT_ID}}"
REGION="${GCP_REGION:-europe-west3}"
SERVICE_NAME="${CLOUD_RUN_SERVICE_NAME:-calendar-insights-demo}"
REPOSITORY_NAME="${ARTIFACT_REGISTRY_REPO:-calendar-insights-repo}"
DB_INSTANCE_NAME="${CLOUD_SQL_INSTANCE_NAME:-calendar-insights-demo-db}"

# Validate required environment variables
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: GOOGLE_CLOUD_PROJECT or GCP_PROJECT_ID environment variable must be set"
    exit 1
fi

IMAGE_NAME="${GCP_REGION:-europe-west3}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY_NAME}/${SERVICE_NAME}"

echo "🚀 Demo Calendar Insights Deployment"
echo "===================================="
echo "📋 Configuration:"
echo "   Project ID: ${PROJECT_ID}"
echo "   Region: ${REGION}"
echo "   Service Name: ${SERVICE_NAME}"
echo "   DB Instance: ${DB_INSTANCE_NAME}"
echo "   Environment: DEMO"
echo ""

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
    --set-env-vars "POSTGRES_HOST=/cloudsql/${PROJECT_ID}:${REGION}:${DB_INSTANCE_NAME},POSTGRES_PORT=5432,ENVIRONMENT=demo" \
    --set-secrets "POSTGRES_DB=postgres_db:latest,POSTGRES_USER=postgres_user:latest,POSTGRES_PASSWORD=postgres_password:latest" \
    --set-cloudsql-instances ${PROJECT_ID}:${REGION}:${DB_INSTANCE_NAME}

# Update database schema
echo "🔧 Updating database schema..."
gcloud run jobs create schema-update-demo-job \
    --image $IMAGE_NAME \
    --region $REGION \
    --set-env-vars "POSTGRES_HOST=/cloudsql/${PROJECT_ID}:${REGION}:${DB_INSTANCE_NAME},POSTGRES_PORT=5432,ENVIRONMENT=demo" \
    --set-secrets "POSTGRES_DB=postgres_db:latest,POSTGRES_USER=postgres_user:latest,POSTGRES_PASSWORD=postgres_password:latest" \
    --set-cloudsql-instances ${PROJECT_ID}:${REGION}:${DB_INSTANCE_NAME} \
    --command python3 \
    --args "update_schema.py" \
    --task-timeout 300 \
    2>/dev/null || echo "Schema update job already exists"

gcloud run jobs execute schema-update-demo-job --region $REGION --wait

# Create/update demo fetch job
echo "🔄 Setting up demo data fetching job..."
gcloud run jobs create demo-fetch-job \
    --image $IMAGE_NAME \
    --region $REGION \
    --set-env-vars "POSTGRES_HOST=/cloudsql/${PROJECT_ID}:${REGION}:${DB_INSTANCE_NAME},POSTGRES_PORT=5432,ENVIRONMENT=demo" \
    --set-secrets "POSTGRES_DB=postgres_db:latest,POSTGRES_USER=postgres_user:latest,POSTGRES_PASSWORD=postgres_password:latest" \
    --set-cloudsql-instances ${PROJECT_ID}:${REGION}:${DB_INSTANCE_NAME} \
    --command python3 \
    --args "dynamic_fetch.py" \
    --task-timeout 1800 \
    --memory 2Gi \
    --cpu 2 \
    2>/dev/null || echo "Demo fetch job already exists"

# Fetch demo data (last 30 days)
echo "📚 Fetching demo data (last 30 days)..."
gcloud run jobs execute demo-fetch-job \
    --region $REGION \
    --args="--days 30" \
    --wait

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo ""
echo "🎉 DEMO DEPLOYMENT COMPLETED SUCCESSFULLY!"
echo "==========================================="
echo ""
echo "📊 Demo Dashboard URL: $SERVICE_URL"
echo ""
echo "🔧 DEMO MANAGEMENT COMMANDS:"
echo "  Fetch last 30 days: gcloud run jobs execute demo-fetch-job --region $REGION --args='--days 30'"
echo "  Fetch last 7 days:  gcloud run jobs execute demo-fetch-job --region $REGION --args='--days 7'"
echo "  Fetch last 90 days: gcloud run jobs execute demo-fetch-job --region $REGION --args='--days 90'"
echo ""
echo "📈 DEMO DATA STATUS:"
echo "  - Historical data: Last 30 days"
echo "  - Environment: Demo"
echo "  - Purpose: Testing and demonstration"
echo ""
echo "🧪 Testing demo deployment..."
echo "Checking service health..."
if curl -s --max-time 30 "$SERVICE_URL" > /dev/null; then
    echo "✅ Demo service is responding successfully!"
else
    echo "⚠️  Demo service might still be starting up. Please wait a moment and try accessing the dashboard."
fi

echo ""
echo "✨ Your Calendar Insights demo is ready!"
echo ""
echo "💡 Demo Features:"
echo "  - Lightweight deployment for testing"
echo "  - Last 30 days of calendar data"
echo "  - Separate from production environment"
echo "  - Perfect for demonstrations and testing" 