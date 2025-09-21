# 🚀 Calendar Insights - Complete Setup Guide

This guide will help you set up Calendar Insights from scratch, whether you're deploying to the cloud or running locally.

## 📋 Prerequisites

### Required Accounts & Services
- **Google Cloud Platform** account (for cloud deployment)
- **Google Workspace** admin access (for calendar data)
- **Google AI Studio** account (for AI Chat Assistant)

### Required Tools
- **Docker** (for local development)
- **gcloud CLI** (for cloud deployment)
- **Git** (for cloning the repository)

## 🎯 Quick Start (5 minutes)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd calendar-insights/app-gcp
```

### 2. Run the Unified Deploy Script
```bash
./deploy.sh
```

### 3. Follow the Interactive Setup
The script will guide you through:
- Environment configuration
- Deployment type selection (Local/Cloud/AI)
- AI Chat Assistant setup

## 🔧 Detailed Setup

### Step 1: Environment Configuration

1. **Copy the environment template**:
   ```bash
   cp env.template .env
   ```

2. **Generate secure passwords and configure**:
   ```bash
   # Generate a secure database password (REQUIRED)
   echo "POSTGRES_PASSWORD=$(openssl rand -base64 32)" >> .env
   
   # Set your Google AI API key
   echo "GOOGLE_API_KEY=your-google-ai-api-key" >> .env
   
   # Set your Google Cloud Project
   echo "GOOGLE_CLOUD_PROJECT=your-project-id" >> .env
   
   # Optional (with defaults)
   echo "GCP_REGION=europe-west3" >> .env
   echo "POSTGRES_USER=dev_user" >> .env
   echo "POSTGRES_DB=calendar_insights" >> .env
   ```

3. **⚠️ Security Requirements**:
   - **NO DEFAULT PASSWORDS** - Always set your own
   - Use strong, unique passwords for each environment
   - Never commit `.env` files to version control
   - See [SECURITY.md](SECURITY.md) for detailed security guidelines

### Step 2: Google Cloud Setup

1. **Create a GCP Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project
   - Note the project ID

2. **Enable Required APIs**:
   ```bash
   gcloud services enable calendar-json.googleapis.com
   gcloud services enable run.googleapis.com
   gcloud services enable sqladmin.googleapis.com
   gcloud services enable secretmanager.googleapis.com
   ```

3. **Set up Authentication**:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

### Step 3: Google Calendar API Setup

1. **Enable Calendar API**:
   - Go to [Google Cloud Console > APIs & Services](https://console.cloud.google.com/apis/library)
   - Search for "Google Calendar API"
   - Click "Enable"

2. **Create OAuth2 Credentials**:
   - Go to [APIs & Services > Credentials](https://console.cloud.google.com/apis/credentials)
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Web application"
   - Add authorized redirect URIs:
     - `http://localhost:8080` (for local development)
     - `https://your-service-url.run.app` (for cloud deployment)

3. **Download Credentials**:
   - Download the JSON file
   - Place it in `credentials/` directory
   - Rename to `oauth2_calendar_service.json`

### Step 4: AI Chat Assistant Setup

1. **Get Google AI API Key**:
   - Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Create a new API key
   - Copy the key

2. **Add to Environment**:
   ```bash
   echo "GOOGLE_API_KEY=your-api-key-here" >> .env
   ```

## 🚀 Deployment Options

### Option 1: Local Development (Recommended for Testing)

```bash
# Run the unified deployment script
./deploy.sh local

# Access the application
open http://localhost:8080
```

**Features:**
- ✅ Full functionality
- ✅ PostgreSQL database
- ✅ AI Chat Assistant
- ✅ Easy debugging
- ❌ No cloud features

#### Local Development Details

**Prerequisites:**
- Docker and Docker Compose installed
- At least 4GB RAM available
- Ports 8080 and 5432 available

**What the script does:**
- Checks all prerequisites
- Creates necessary directories and files
- Builds the Docker image
- Starts PostgreSQL database
- Starts the application
- Generates test data
- Provides access URLs and commands

**Useful Commands:**
```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Access database
docker-compose exec postgres psql -U dev_user -d calendar_insights

# Regenerate test data
docker-compose exec app-gcp python generate_test_data.py
```

### Option 2: Google Cloud Run (Recommended for Production)

```bash
# Deploy to Google Cloud
./deploy.sh cloud

# The script will provide the service URL
```

**Features:**
- ✅ Auto-scaling
- ✅ Managed database
- ✅ Scheduled data fetching
- ✅ Secret management
- ✅ Production-ready

### Option 3: Demo Deployment (Automated)

For automated demo deployments that stay up-to-date with your main branch:

```bash
# Set up demo environment (one-time)
./deploy.sh cloud --demo

# Demo automatically updates when you push to main branch
git push origin main
```

**Demo Features:**
- ✅ Automatic updates from main branch
- ✅ Lightweight deployment optimized for demos
- ✅ Separate environment isolated from production
- ✅ Perfect for testing new features
- ✅ 30 days of sample data included

**Demo Architecture:**
```
Main Branch → GitHub Actions → GCP Cloud Run → Demo Environment
     ↓              ↓              ↓              ↓
   Code         CI/CD         Container      Demo App
   Changes      Pipeline      Deployment     (30 days data)
```

### Option 4: Manual Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## 🔍 Verification

### Check Application Status
```bash
# Local deployment
curl http://localhost:8080

# Cloud deployment
curl https://your-service-url.run.app
```

### Test AI Chat Assistant
1. Open the application in your browser
2. Click "🤖 AI Chat Assistant"
3. Ask: "How many meetings do we have?"
4. Verify you get a data-driven response

### Test Data Fetching
```bash
# Check if data is being fetched
python generate_test_data.py

# Verify database connection
python init_db_standalone.py test
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. "Missing environment variables"
```bash
# Check your .env file
cat .env

# Verify required variables are set
python -c "
import os
required = ['GOOGLE_CLOUD_PROJECT', 'POSTGRES_PASSWORD', 'GOOGLE_API_KEY']
missing = [v for v in required if not os.getenv(v)]
print('✅ All set' if not missing else f'❌ Missing: {missing}')
"
```

#### 2. "Database connection failed"
```bash
# For local development
docker-compose restart postgres

# For cloud deployment
gcloud sql instances describe calendar-insights-db
```

#### 3. "AI Chat not working"
```bash
# Verify API key is set
echo $GOOGLE_API_KEY

# Test API key
curl -H "Authorization: Bearer $GOOGLE_API_KEY" \
     https://generativelanguage.googleapis.com/v1/models
```

#### 4. "Calendar API access denied"
- Check OAuth2 credentials are properly configured
- Verify the service account has Calendar API access
- Ensure the redirect URIs match your deployment

### Debug Commands

```bash
# Test environment setup
./scripts/test_local_setup.py

# Check Docker containers
docker-compose ps

# View application logs
docker-compose logs app-gcp

# Test database connection
python database.py test
```

## 📚 Next Steps

### 1. Configure Data Fetching
```bash
# Set up automated data fetching
./scripts/generate-data.sh

# Or run manually
python dynamic_fetch.py --days 30
```

### 2. Customize the Dashboard
- Edit `dashboard.py` for UI changes
- Modify `ai_agent.py` for AI behavior
- Update `database.py` for data processing

### 3. Set up Monitoring
- Configure Cloud Monitoring (for cloud deployment)
- Set up log aggregation
- Create alerts for system health

## 🆘 Getting Help

- **Documentation**: Check the README.md files in each directory
- **Issues**: Report bugs on GitHub/GitLab issues
- **Discussions**: Ask questions in the discussions section

## 🎉 Success!

If everything is working correctly, you should see:
- ✅ Application accessible in browser
- ✅ AI Chat Assistant responding to questions
- ✅ Meeting data being displayed
- ✅ No error messages in logs

Welcome to Calendar Insights! 🎊
