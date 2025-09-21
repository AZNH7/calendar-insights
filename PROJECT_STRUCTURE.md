# 📁 Calendar Insights - Project Structure

This document provides an overview of the Calendar Insights project structure and explains the purpose of each directory and file.

## 🏗️ Repository Structure

```
calendar-insights/
├── 📄 README.md                    # Main project documentation
├── 📄 SETUP_GUIDE.md              # Complete setup guide for new users
├── 📄 CONTRIBUTING.md             # Contribution guidelines
├── 📄 LICENSE                     # MIT License
├── 📄 .gitignore                  # Git ignore rules
├── 📄 PROJECT_STRUCTURE.md        # This file
│
├── 📁 app/                        # Self-hosted application (Enterprise)
│   ├── 📄 README.md              # Enterprise app documentation
│   ├── 📄 requirements.txt       # Python dependencies
│   ├── 📄 docker-compose.yml     # Docker Compose configuration
│   ├── 📄 Dockerfile             # Docker image definition
│   ├── 📄 dashboard.py           # Main dashboard application
│   ├── 📄 database.py            # Database operations
│   ├── 📄 fetch_data.py          # Data fetching logic
│   └── 📁 config/                # Configuration files
│
├── 📁 app-gcp/                    # Cloud application (Production)
│   ├── 📄 README.md              # Cloud app documentation
│   ├── 📄 deploy.sh              # Easy deployment script
│   ├── 📄 requirements.txt       # Python dependencies
│   ├── 📄 docker-compose.yml     # Local development Docker setup
│   ├── 📄 Dockerfile             # Docker image definition
│   ├── 📄 dashboard.py           # Main Streamlit dashboard
│   ├── 📄 ai_agent.py            # AI Chat Assistant
│   ├── 📄 database.py            # Database operations
│   ├── 📄 calendar_service.py    # Google Calendar integration
│   ├── 📄 dynamic_fetch.py       # Data fetching with scheduling
│   ├── 📄 env.template           # Environment variables template
│   │
│   ├── 📁 pages/                 # Streamlit pages
│   │   └── 📄 ai_chat.py         # AI Chat Assistant page
│   │
│   ├── 📁 scripts/               # Specialized deployment scripts
│   │   ├── 📄 cloud-deploy.sh          # Advanced cloud deployment
│   │   └── 📄 README.md                # Scripts documentation
│   │
│   ├── 📁 credentials/           # Authentication templates
│   │   ├── 📄 README.md          # Credentials setup guide
│   │   ├── 📄 service-account.json.template
│   │   └── 📄 oauth2_calendar_service.py
│   │
│   └── 📁 config/                # Configuration files
│
└── 📁 docs/                      # Additional documentation
    ├── 📄 AI_CHAT_FEATURE.md     # AI Chat Assistant documentation
    └── 📄 DEMO_DEPLOYMENT.md     # Demo deployment guide
```

## 🎯 Application Types

### ☁️ Cloud Application (`app-gcp/`)
**Purpose**: Production-ready, cloud-native deployment on Google Cloud Platform

**Key Features**:
- ✅ Serverless Cloud Run deployment
- ✅ Managed Cloud SQL PostgreSQL
- ✅ AI Chat Assistant with Google ADK
- ✅ Automated data fetching with Cloud Scheduler
- ✅ Secret Manager integration
- ✅ Auto-scaling capabilities

**Best For**:
- Production deployments
- Teams wanting cloud-native solutions
- Organizations with GCP infrastructure
- Quick setup and deployment

### 🏢 Self-Hosted Application (`app/`)
**Purpose**: Enterprise self-hosted deployment with advanced features

**Key Features**:
- ✅ Self-hosted deployment
- ✅ Advanced user directory integration
- ✅ Custom authentication systems
- ✅ Enterprise-grade security
- ✅ Full control over infrastructure

**Best For**:
- Enterprise environments
- Organizations requiring full control
- Custom infrastructure requirements
- Advanced security needs

## 📋 Key Files Explained

### 🚀 Deployment Scripts
- **`deploy.sh`**: Unified deployment script for all scenarios
- **`scripts/cloud-deploy.sh`**: Advanced cloud deployment (for experts)
- **`generate-data.sh`**: Data generation and management utilities

### 🔧 Configuration Files
- **`env.template`**: Environment variables template
- **`docker-compose.yml`**: Local development Docker setup
- **`Dockerfile`**: Container image definition
- **`requirements.txt`**: Python dependencies

### 📊 Application Files
- **`dashboard.py`**: Main Streamlit application
- **`ai_agent.py`**: AI Chat Assistant implementation
- **`database.py`**: Database operations and queries
- **`calendar_service.py`**: Google Calendar API integration
- **`dynamic_fetch.py`**: Automated data fetching

### 📚 Documentation
- **`README.md`**: Main project documentation
- **`SETUP_GUIDE.md`**: Complete setup guide
- **`CONTRIBUTING.md`**: Contribution guidelines
- **`LOCAL_DEVELOPMENT.md`**: Local development guide

## 🔐 Security & Credentials

### Credential Templates
All credential files are provided as templates to ensure security:
- `credentials/service-account.json.template`
- `credentials/oauth2_calendar_service.py`

### Environment Variables
Sensitive information is managed through environment variables:
- Database credentials
- API keys
- OAuth2 client secrets
- Google Cloud project settings

## 🚀 Getting Started

### For New Users
1. Start with the [SETUP_GUIDE.md](SETUP_GUIDE.md)
2. Choose your deployment type (Cloud or Self-hosted)
3. Follow the interactive setup with `deploy.sh`

### For Developers
1. Read [CONTRIBUTING.md](CONTRIBUTING.md)
2. Set up local development environment
3. Check the specific README in your chosen app directory

### For Enterprise
1. Review the `app/` directory for self-hosted options
2. Check enterprise features and requirements
3. Contact support for custom deployment assistance

## 🔄 Maintenance

### Regular Updates
- Keep dependencies updated in `requirements.txt`
- Monitor security updates for Docker images
- Update environment templates as needed

### Monitoring
- Check application logs regularly
- Monitor database performance
- Review AI Chat Assistant usage patterns

## 📞 Support

- **Documentation**: Check README files in each directory
- **Issues**: Report on GitHub/GitLab issues
- **Discussions**: Ask questions in project discussions
- **Setup Help**: Follow the SETUP_GUIDE.md step by step

---

This structure is designed to be intuitive, secure, and maintainable. Each component has a clear purpose and the documentation provides guidance for different use cases and deployment scenarios.
