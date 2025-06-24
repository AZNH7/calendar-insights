# ☁️ Calendar Insights - Cloud Application

> Google Cloud Run optimized version with auto-scaling and cloud-native features. For enterprise/AWS deployment, see the `app/` directory.

## 🚀 Quick Deploy

```bash
./deploy-with-options.sh
```

## 📋 Features

- **Serverless**: Auto-scaling Cloud Run deployment
- **Cloud SQL**: Managed PostgreSQL database
- **Scheduled Fetching**: Automated data collection via Cloud Scheduler
- **Secret Management**: Secure credential storage
- **Multi-Environment**: Production, staging, development support

## 🔒 CI/CD Setup & Security

### Required Environment Variables

All sensitive information must be stored as **environment variables** in your CI/CD platform. No hardcoded credentials are present in the codebase.

#### Essential Variables (Must be set in CI/CD)

| Variable | Description | Secret? |
|----------|-------------|---------|
| `GOOGLE_CLOUD_PROJECT` | GCP Project ID | ✅ |
| `POSTGRES_PASSWORD` | Database password | ✅ |
| `POSTGRES_USER` | Database username | ✅ |
| `POSTGRES_DB` | Database name | ✅ |
| `GOOGLE_CLIENT_SECRET` | OAuth client secret | ✅ |
| `GOOGLE_CLIENT_ID` | OAuth client ID | ✅ |
| `SECRET_KEY` | App security key | ✅ |

#### Optional Variables (with defaults)

| Variable | Description | Default |
|----------|-------------|---------|
| `GCP_REGION` | Deployment region | `europe-west3` |
| `CLOUD_RUN_SERVICE_NAME` | Service name | `calendar-insights` |
| `CLOUD_SQL_INSTANCE_NAME` | Database instance | `calendar-insights-db` |
| `ARTIFACT_REGISTRY_REPO` | Docker repo | `calendar-insights-repo` |

### GitLab CI Setup

1. **Set Variables** in Project Settings > CI/CD > Variables:
   ```yaml
   # Protected and Masked variables
   GOOGLE_CLOUD_PROJECT: your-project-id
   POSTGRES_PASSWORD: your-secure-password
   POSTGRES_USER: your-db-user
   POSTGRES_DB: your-database-name
   GOOGLE_CLIENT_SECRET: your-oauth-secret
   GOOGLE_CLIENT_ID: your-client-id
   SECRET_KEY: your-app-secret-key
   ```

2. **Create `.gitlab-ci.yml`**:
   ```yaml
   stages:
     - build
     - deploy
   
   before_script:
     - echo $GOOGLE_SERVICE_ACCOUNT_KEY | base64 -d > gcloud-service-key.json
     - gcloud auth activate-service-account --key-file gcloud-service-key.json
     - gcloud config set project $GOOGLE_CLOUD_PROJECT
   
   deploy:
     stage: deploy
     image: google/cloud-sdk:latest
     script:
       - cd app-gcp
       - export POSTGRES_HOST="/cloudsql/$GOOGLE_CLOUD_PROJECT:$GCP_REGION:$CLOUD_SQL_INSTANCE_NAME"
       - bash deploy-with-options.sh
     only:
       - main
   ```

### GitHub Actions Setup

1. **Set Repository Secrets** in Settings > Secrets and Variables > Actions
2. **Create `.github/workflows/deploy.yml`**:
   ```yaml
   name: Deploy to Google Cloud Run
   on:
     push:
       branches: [main]
   
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
       - uses: actions/checkout@v3
       - uses: google-github-actions/setup-gcloud@v1
         with:
           service_account_key: ${{ secrets.GOOGLE_SERVICE_ACCOUNT_KEY }}
           project_id: ${{ secrets.GOOGLE_CLOUD_PROJECT }}
       - name: Deploy
         working-directory: ./app-gcp
         env:
           GOOGLE_CLOUD_PROJECT: ${{ secrets.GOOGLE_CLOUD_PROJECT }}
           POSTGRES_PASSWORD: ${{ secrets.POSTGRES_PASSWORD }}
           # ... other secrets
         run: bash deploy-with-options.sh
   ```

### Security Best Practices

✅ **DO:**
- Store all sensitive data in CI/CD environment variables
- Use Secret Manager for production deployments
- Mark variables as protected and masked in GitLab
- Regularly rotate passwords and API keys

❌ **DON'T:**
- Commit credentials to version control
- Use default passwords in production
- Share service account keys in plain text
- Log sensitive information

## ⚙️ Configuration

### Environment Variables Template

See `env.template` for a complete list of configurable environment variables.

### Deployment Options
```bash
# Fresh deployment (recommended)
./deploy-with-options.sh --fresh

# Update existing deployment
./deploy-with-options.sh --update

# Development deployment
./deploy-with-options.sh --dev
```

## 🔧 Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (set environment variables first)
streamlit run dashboard.py --server.port=8080

# Build container
docker build -t calendar-insights .
docker run -p 8080:8080 calendar-insights
```

## 📊 Data Management

### Historical Data Import
```bash
# Import 3 years of data
gcloud run jobs execute dynamic-fetch-job --region europe-west3 --args='--years 3'

# Daily update (automated via Cloud Scheduler)
gcloud run jobs execute dynamic-fetch-job --region europe-west3 --args='--daily'
```

### Database Operations
```bash
# Initialize database
python init_db_standalone.py

# Update schema
python update_schema.py

# Cleanup old data
python cleanup_database.py --days 90
```

## 🌍 Access

- **Production**: Deployed via Cloud Run (URL provided after deployment)
- **Local Development**: http://localhost:8080

## 🔍 Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   ```
   ❌ Missing required environment variables: POSTGRES_PASSWORD
   ```
   **Solution:** Ensure all required variables are set in CI/CD

2. **Database Connection Issues**
   ```
   ❌ Connection failed: connection to server failed
   ```
   **Solution:** Check Cloud SQL instance is running and environment variables are correct

### Debug Commands

```bash
# Test environment variables (without exposing values)
python3 -c "import os; print('✓' if os.getenv('POSTGRES_PASSWORD') else '❌ POSTGRES_PASSWORD missing')"

# Test database connection
python3 init_db_standalone.py test

# Validate all required variables
python3 -c "
import os
required = ['GOOGLE_CLOUD_PROJECT', 'POSTGRES_HOST', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD']
missing = [v for v in required if not os.getenv(v)]
print('✅ All variables set' if not missing else f'❌ Missing: {missing}')
"
```

## 🚀 Quick Migration to Enterprise

To upgrade to the enterprise self-hosted version with AWS and advanced features:

```bash
# Switch to enterprise version
cd ../app

# Configure AWS RDS
export DB_HOST=your-rds-endpoint.rds.amazonaws.com
export AWS_REGION=us-east-1

# Deploy with AWS backend
docker-compose up -d
```

See `../app/README.md` for full enterprise features including user directory integration and AWS deployment. 