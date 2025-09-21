# 📅 Calendar Insights

[![Security](https://img.shields.io/badge/security-verified-green)](https://github.com/your-org/calendar-insights)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://docker.com)
[![Cloud Run](https://img.shields.io/badge/cloud%20run-deployed-blue)](https://cloud.google.com/run)

> Transform your Google Calendar data into actionable meeting insights with beautiful analytics dashboards.

## ✨ Features

🔍 **Meeting Analytics** - Daily, weekly, monthly trends and patterns  
👥 **Participant Insights** - Department and team collaboration analysis  
📊 **Interactive Dashboard** - Filter by time, departments, meeting types  
📈 **Export Reports** - CSV downloads and visual report generation  
⚡ **Real-time Updates** - Automated data fetching and synchronization  
🔒 **Enterprise Security** - OAuth2 integration with Google Workspace  

## 🚀 Quick Deploy

### Option 1: Cloud Deployment (Recommended)
```bash
git clone <repository-url>
cd calendar-insights/app-gcp
./deploy-with-options.sh
```
Access at: `https://your-service-url.run.app`



## 🎯 Deployment Options

| Method | Best For | Setup Time | Scalability | Platform |
|--------|----------|------------|-------------|----------|
| **GitHub Actions** | Teams, automation | 5 min | Auto-scaling | GCP |
| **Local Docker** | Development, testing | 2 min | Single instance | Local |
| **Manual GCP** | Production, control | 10 min | Full cloud | GCP |


### GitHub Actions (Automated)
1. Go to **Actions** → **Run workflow**
2. Choose your options:
   - ✅ Deploy cloud app (`app-gcp/`)
   - ⚠️ Deploy self-hosted app (`app/`) - **TBD: Under Development**
   - 🎯 Select environment (prod/dev/staging)
3. Click **Run workflow**

**Results:**
- Cloud app → Auto-deployed to Google Cloud Run
- Self-hosted app → **TBD** - Currently under development

### Manual Commands
```bash
# Cloud deployment
cd app-gcp && ./deploy-with-options.sh



# Development mode
cd app-gcp && streamlit run dashboard.py
```

## ⚙️ Configuration

### Prerequisites
- Google Cloud Platform account (for app-gcp)
- Google Workspace admin access
- Docker installed

### Required Secrets
Set these in your deployment method:
- `GCP_SERVICE_ACCOUNT_KEY` - Google Cloud credentials
- `POSTGRES_PASSWORD` - Database password

### Google Calendar Setup
1. Enable Google Calendar API in [Google Cloud Console](https://console.cloud.google.com)
2. Create OAuth2 credentials
3. Add authorized redirect URIs
4. Download credentials to `app-gcp/credentials/`

## 🏗️ Architecture

```mermaid
graph TD
    A[Google Calendar API] --> B[Data Fetcher]
    B --> C[PostgreSQL Database]
    C --> D[Streamlit Dashboard]
    E[Cloud Scheduler] --> B
    F[Cloud Run] --> D
    
    I[Google Workspace] --> J[User Directory]
    J --> K[Identity Cross-Reference]
```

**Components:**
- **Cloud App** (`app-gcp/`) - Production-ready, serverless, auto-scaling on GCP

## 📊 Application Comparison

### ☁️ Cloud App (`app-gcp/`) - GCP Serverless
- **Platform**: Google Cloud Run + Cloud SQL
- **Scaling**: Automatic serverless scaling
- **Database**: Cloud SQL PostgreSQL
- **Best For**: Quick deployment, cloud-native teams
- **Features**: 
  - Streamlined calendar analytics
  - Automated daily data fetching
  - Cloud Scheduler integration
  - Secret Manager security





## 🛠️ Development

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r app-gcp/requirements.txt

# Run locally
cd app-gcp
streamlit run dashboard.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

## 🆘 Support

- **Issues**: [GitHub Issues](../../issues)
- **Wiki**: [Project Documentation](../../wiki)
