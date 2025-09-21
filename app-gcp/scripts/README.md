# 📁 Scripts Directory

This directory contains specialized deployment and utility scripts for Calendar Insights.

## 🚀 Main Deployment

**Use the main deployment script instead of these individual scripts:**

```bash
# From the app-gcp directory
./deploy.sh
```

## 📋 Available Scripts

### `cloud-deploy.sh`
Advanced Google Cloud Run deployment script with full configuration options.

**Usage:**
```bash
./scripts/cloud-deploy.sh
```

**Features:**
- Complete GCP infrastructure setup
- Cloud SQL database creation
- Secret Manager integration
- Cloud Run deployment
- CI/CD configuration

## 🔧 Utility Scripts

### `generate-data.sh` (moved to app-gcp root)
Data generation and management utilities.

## 📚 Documentation

- **Main Setup**: Use `./deploy.sh` for all deployment scenarios
- **Local Development**: `./deploy.sh local`
- **Cloud Deployment**: `./deploy.sh cloud`
- **AI Setup**: `./deploy.sh ai`

## ⚠️ Note

The main `deploy.sh` script in the app-gcp root directory is the recommended way to deploy Calendar Insights. These scripts are provided for advanced users who need specific functionality.
