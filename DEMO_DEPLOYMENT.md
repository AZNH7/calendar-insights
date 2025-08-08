# Calendar Insights - Demo Deployment Guide

This guide explains how to set up automated demo deployments that stay up-to-date with your main branch.

## 🎯 Overview

The demo deployment system automatically deploys a lightweight version of your Calendar Insights application whenever the main branch is updated. This provides:

- **Automatic updates**: Demo stays current with main branch
- **Lightweight deployment**: Optimized for demonstrations and testing
- **Separate environment**: Isolated from production
- **Quick iteration**: Perfect for testing new features

## 🏗️ Architecture

```
Main Branch → GitHub Actions → GCP Cloud Run → Demo Environment
     ↓              ↓              ↓              ↓
   Code         CI/CD         Container      Demo App
   Changes      Pipeline      Deployment     (30 days data)
```

## 📋 Prerequisites

### 1. Google Cloud Platform Setup

Ensure you have:
- A GCP project with billing enabled
- Cloud Run API enabled
- Cloud SQL API enabled
- Artifact Registry API enabled
- Service account with appropriate permissions

### 2. Required GCP Resources

The demo deployment will create/use:
- **Cloud Run Service**: `calendar-insights-demo`
- **Cloud SQL Instance**: `calendar-insights-demo-db`
- **Artifact Registry**: `calendar-insights-repo`
- **Cloud Run Jobs**: `schema-update-demo-job`, `demo-fetch-job`

## 🔧 Setup Instructions

### Step 1: Create GCP Service Account

```bash
# Create service account
gcloud iam service-accounts create calendar-insights-demo \
    --display-name="Calendar Insights Demo Service Account"

# Grant necessary roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:calendar-insights-demo@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:calendar-insights-demo@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:calendar-insights-demo@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

# Create and download key
gcloud iam service-accounts keys create demo-service-account.json \
    --iam-account=calendar-insights-demo@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### Step 2: Set Up GitHub Secrets

In your GitHub repository, go to **Settings > Secrets and variables > Actions** and add:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `GCP_PROJECT_ID` | Your GCP Project ID | `my-calendar-project` |
| `GCP_SA_KEY` | Base64 encoded service account key | `base64 -i demo-service-account.json` |
| `POSTGRES_PASSWORD` | Demo database password | `your-secure-password` |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | `your-google-secret` |
| `SECRET_KEY` | Application secret key | `your-app-secret` |

### Step 3: Create Demo Database

```bash
# Create Cloud SQL instance for demo
gcloud sql instances create calendar-insights-demo-db \
    --database-version=POSTGRES_14 \
    --tier=db-f1-micro \
    --region=europe-west3 \
    --storage-type=SSD \
    --storage-size=10GB

# Create database
gcloud sql databases create calendar_insights_demo \
    --instance=calendar-insights-demo-db

# Create user
gcloud sql users create calendar_demo_user \
    --instance=calendar-insights-demo-db \
    --password=YOUR_DEMO_PASSWORD

# Store password in Secret Manager
echo -n "YOUR_DEMO_PASSWORD" | gcloud secrets create postgres_password --data-file=-
```

### Step 4: Enable GitHub Actions

The workflow is already configured in `.github/workflows/demo-deploy.yml`. It will automatically:

1. Trigger on pushes to main branch
2. Build and push Docker image
3. Deploy to Cloud Run
4. Update database schema
5. Fetch demo data (last 30 days)

## 🚀 Manual Deployment

If you want to deploy the demo manually:

```bash
# Set environment variables
export GOOGLE_CLOUD_PROJECT=your-project-id
export GCP_REGION=europe-west3

# Run demo deployment
cd app-gcp
chmod +x deploy-demo.sh
./deploy-demo.sh
```

## 📊 Demo Environment Features

### Data Configuration
- **Historical Data**: Last 30 days only
- **Update Frequency**: Manual or on-demand
- **Data Limits**: Optimized for demo purposes

### Performance Settings
- **Memory**: 2GB
- **CPU**: 2 cores
- **Timeout**: 15 minutes
- **API Rate Limits**: Reduced for demo

### Security
- **Authentication**: Unauthenticated access
- **Database**: Separate demo instance
- **Secrets**: Managed via Secret Manager

## 🔄 Automation Workflow

### Automatic Triggers
- **Push to main**: Deploys new demo version
- **Manual trigger**: Available via GitHub Actions UI

### Deployment Process
1. **Code Checkout**: Latest main branch
2. **Docker Build**: Create container image
3. **Cloud Run Deploy**: Update demo service
4. **Schema Update**: Ensure database compatibility
5. **Data Fetch**: Load last 30 days of data
6. **Health Check**: Verify deployment success

## 📈 Monitoring and Management

### View Demo Status
```bash
# Check service status
gcloud run services describe calendar-insights-demo --region=europe-west3

# View logs
gcloud run services logs read calendar-insights-demo --region=europe-west3

# Check jobs
gcloud run jobs list --region=europe-west3
```

### Update Demo Data
```bash
# Fetch last 30 days
gcloud run jobs execute demo-fetch-job --region=europe-west3 --args="--days 30"

# Fetch last 7 days
gcloud run jobs execute demo-fetch-job --region=europe-west3 --args="--days 7"

# Fetch last 90 days
gcloud run jobs execute demo-fetch-job --region=europe-west3 --args="--days 90"
```

### Demo URL
The demo will be available at:
```
https://calendar-insights-demo-xxxxx-ew.a.run.app
```

## 🛠️ Troubleshooting

### Common Issues

1. **Deployment Fails**
   - Check GitHub Actions logs
   - Verify GCP permissions
   - Ensure secrets are correctly set

2. **Database Connection Issues**
   - Verify Cloud SQL instance is running
   - Check connection string format
   - Ensure service account has Cloud SQL Client role

3. **Data Fetching Issues**
   - Check Google API credentials
   - Verify OAuth client configuration
   - Review API rate limits

### Debug Commands
```bash
# Check service account permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID \
    --flatten="bindings[].members" \
    --format='table(bindings.role)' \
    --filter="bindings.members:calendar-insights-demo"

# Test database connection
gcloud sql connect calendar-insights-demo-db --user=calendar_demo_user

# View recent deployments
gcloud run revisions list --service=calendar-insights-demo --region=europe-west3
```

## 🔐 Security Considerations

### Demo Environment Security
- **Isolated Database**: Separate from production
- **Limited Permissions**: Minimal required access
- **No Sensitive Data**: Demo data only
- **Temporary Access**: Suitable for demonstrations

### Best Practices
- Regularly rotate demo passwords
- Monitor demo usage and costs
- Clean up old demo data periodically
- Use separate Google API credentials for demo

## 💰 Cost Optimization

### Demo Environment Costs
- **Cloud Run**: ~$5-10/month (depending on usage)
- **Cloud SQL**: ~$7/month (db-f1-micro)
- **Artifact Registry**: Minimal cost
- **Network**: Minimal cost

### Cost Reduction Tips
- Use smaller instance sizes for demo
- Implement auto-scaling to zero
- Clean up unused resources
- Monitor usage patterns

## 📝 Configuration Files

### Key Files
- `.github/workflows/demo-deploy.yml`: CI/CD workflow
- `app-gcp/deploy-demo.sh`: Manual deployment script
- `app-gcp/env.demo.template`: Demo environment template
- `app-gcp/Dockerfile`: Container configuration

### Environment Variables
See `app-gcp/env.demo.template` for all available configuration options.

## 🎉 Next Steps

1. **Set up the prerequisites** (GCP project, service account, etc.)
2. **Configure GitHub secrets** with your values
3. **Push to main branch** to trigger first demo deployment
4. **Test the demo** and verify functionality
5. **Customize as needed** for your specific use case

The demo deployment will now automatically stay up-to-date with your main branch, providing a reliable testing and demonstration environment for your Calendar Insights application. 