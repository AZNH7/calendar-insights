#!/bin/bash

# Calendar Insights Demo Setup Script
# This script helps set up the demo deployment environment

set -e

echo "🚀 Calendar Insights Demo Setup"
echo "==============================="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: Google Cloud CLI (gcloud) is not installed"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Error: Not authenticated with Google Cloud"
    echo "Please run: gcloud auth login"
    exit 1
fi

# Get project ID
echo "📋 Current GCP Configuration:"
echo "   Project: $(gcloud config get-value project)"
echo "   Account: $(gcloud config get-value account)"
echo ""

read -p "Do you want to continue with this project? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please set the correct project with: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

PROJECT_ID=$(gcloud config get-value project)
REGION="europe-west3"

echo ""
echo "🔧 Setting up demo environment for project: $PROJECT_ID"
echo ""

# Enable required APIs
echo "📡 Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Create service account
echo "👤 Creating service account..."
gcloud iam service-accounts create calendar-insights-demo \
    --display-name="Calendar Insights Demo Service Account" \
    2>/dev/null || echo "Service account already exists"

# Grant necessary roles
echo "🔐 Granting permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:calendar-insights-demo@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin" \
    2>/dev/null || echo "Run admin role already granted"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:calendar-insights-demo@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client" \
    2>/dev/null || echo "Cloud SQL client role already granted"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:calendar-insights-demo@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin" \
    2>/dev/null || echo "Storage admin role already granted"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:calendar-insights-demo@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    2>/dev/null || echo "Secret Manager accessor role already granted"

# Create and download service account key
echo "🔑 Creating service account key..."
gcloud iam service-accounts keys create demo-service-account.json \
    --iam-account=calendar-insights-demo@$PROJECT_ID.iam.gserviceaccount.com \
    2>/dev/null || echo "Service account key already exists"

# Create Artifact Registry repository
echo "📦 Creating Artifact Registry repository..."
gcloud artifacts repositories create calendar-insights-repo \
    --repository-format=docker \
    --location=$REGION \
    --description="Calendar Insights Demo Repository" \
    2>/dev/null || echo "Artifact Registry repository already exists"

# Create Cloud SQL instance
echo "🗄️  Creating Cloud SQL instance..."
gcloud sql instances create calendar-insights-demo-db \
    --database-version=POSTGRES_14 \
    --tier=db-f1-micro \
    --region=$REGION \
    --storage-type=SSD \
    --storage-size=10GB \
    --backup-start-time="02:00" \
    2>/dev/null || echo "Cloud SQL instance already exists"

# Create database
echo "📊 Creating database..."
gcloud sql databases create calendar_insights_demo \
    --instance=calendar-insights-demo-db \
    2>/dev/null || echo "Database already exists"

# Generate demo password
DEMO_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# Create database user
echo "👤 Creating database user..."
gcloud sql users create calendar_demo_user \
    --instance=calendar-insights-demo-db \
    --password="$DEMO_PASSWORD" \
    2>/dev/null || echo "Database user already exists"

# Store password in Secret Manager
echo "🔐 Storing password in Secret Manager..."
echo -n "$DEMO_PASSWORD" | gcloud secrets create postgres_password --data-file=- \
    2>/dev/null || echo "Password secret already exists"

# Generate application secret
APP_SECRET=$(openssl rand -base64 32)

# Store app secret
echo -n "$APP_SECRET" | gcloud secrets create app_secret --data-file=- \
    2>/dev/null || echo "App secret already exists"

echo ""
echo "🎉 Demo environment setup completed!"
echo "==================================="
echo ""
echo "📋 Next Steps:"
echo "1. Set up GitHub repository secrets:"
echo "   - GCP_PROJECT_ID: $PROJECT_ID"
echo "   - GCP_SA_KEY: $(base64 -i demo-service-account.json)"
echo "   - POSTGRES_PASSWORD: $DEMO_PASSWORD"
echo "   - SECRET_KEY: $APP_SECRET"
echo "   - GOOGLE_CLIENT_SECRET: (your Google OAuth client secret)"
echo ""
echo "2. Push to main branch to trigger demo deployment"
echo ""
echo "3. Demo will be available at:"
echo "   https://calendar-insights-demo-xxxxx-ew.a.run.app"
echo ""
echo "📁 Generated files:"
echo "   - demo-service-account.json (service account key)"
echo "   - DEMO_DEPLOYMENT.md (setup guide)"
echo ""
echo "🔧 Manual deployment:"
echo "   cd app-gcp && ./deploy-demo.sh"
echo ""
echo "✨ Your demo environment is ready!" 