# 🚀 CI/CD Pipeline Guide

This guide explains the CI/CD pipelines for Calendar Insights on both GitHub and GitLab platforms.

## 📋 Overview

Calendar Insights supports deployment on both GitHub Actions and GitLab CI/CD with comprehensive security scanning, testing, and deployment automation.

## 🔐 Required Secrets

### GitHub Actions Secrets
Set these in your repository: **Settings > Secrets and Variables > Actions**

| Secret | Description | Required For |
|--------|-------------|--------------|
| `GCP_PROJECT_ID` | Google Cloud Project ID | All deployments |
| `GCP_SERVICE_ACCOUNT_KEY` | Base64-encoded service account key | Cloud deployments |
| `POSTGRES_PASSWORD` | Database password | All deployments |
| `GOOGLE_API_KEY` | Google AI API key | AI Chat functionality |
| `GOOGLE_CLIENT_SECRET` | OAuth client secret | Calendar integration |
| `SECRET_KEY` | Application security key | All deployments |

### GitLab CI/CD Variables
Set these in your project: **Settings > CI/CD > Variables**

| Variable | Description | Protected | Masked |
|----------|-------------|-----------|--------|
| `GCP_PROJECT_ID` | Google Cloud Project ID | ✅ | ❌ |
| `GCP_SERVICE_ACCOUNT_KEY` | Base64-encoded service account key | ✅ | ✅ |
| `POSTGRES_PASSWORD` | Database password | ✅ | ✅ |
| `GOOGLE_API_KEY` | Google AI API key | ✅ | ✅ |
| `GOOGLE_CLIENT_SECRET` | OAuth client secret | ✅ | ✅ |
| `SECRET_KEY` | Application security key | ✅ | ✅ |

## 🔄 Pipeline Stages

### 1. Security Scanning
- **TruffleHog OSS**: Detects hardcoded secrets
- **Custom Secret Detection**: Scans for password/API key patterns
- **GitLab Secret Detection**: Built-in secret scanning
- **File Validation**: Ensures .gitignore is present

### 2. Code Quality
- **Black**: Code formatting check
- **isort**: Import sorting check
- **Flake8**: Linting and error detection
- **Import Testing**: Validates Python module imports

### 3. Testing
- **Syntax Validation**: Ensures all Python files are valid
- **Import Testing**: Tests critical module imports
- **Docker Smoke Tests**: Basic container functionality

### 4. Building
- **Docker Image Build**: Creates production-ready images
- **Multi-Platform Support**: Builds for both `app/` and `app-gcp/`
- **Image Tagging**: Tags with commit SHA and latest

### 5. Deployment

#### Automatic Deployments
- **main branch** → `app-gcp` to Google Cloud Run (production)
- **develop branch** → Development artifacts ready

#### Manual Deployments
- **GitHub**: Use workflow_dispatch with parameters
- **GitLab**: Use manual jobs with variables

## 🚀 Deployment Options

### Option 1: GitHub Actions

#### Automatic Deployment
```bash
# Push to main branch triggers production deployment
git push origin main
```

#### Manual Deployment
1. Go to **Actions** tab
2. Select **Calendar Insights CI/CD** workflow
3. Click **Run workflow**
4. Configure parameters:
   - Deploy app-gcp: ✅
   - Environment: production
   - Force rebuild: false

#### Demo Deployment
```bash
# Push to main triggers demo deployment
git push origin main
```

### Option 2: GitLab CI/CD

#### Automatic Deployment
```bash
# Push to main branch triggers production deployment
git push origin main
```

#### Manual Deployment
1. Go to **CI/CD > Pipelines**
2. Click **Run pipeline**
3. Set variables:
   - `DEPLOY_APP_GCP=true`
   - `DEPLOY_ENVIRONMENT=production`

#### Manual Jobs
- **manual-deploy-app-gcp**: Deploy to Google Cloud Run
- **manual-deploy-app**: Prepare self-hosted deployment

## 🔧 Pipeline Configuration

### Environment Variables

#### GitHub Actions
```yaml
env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  REGION: europe-west3
```

#### GitLab CI/CD
```yaml
variables:
  PROJECT_ID: $GCP_PROJECT_ID
  REGION: "europe-west3"
  SERVICE_NAME: "calendar-insights"
```

### Deployment Environments

| Environment | Branch | Target | URL |
|-------------|--------|--------|-----|
| **Production** | main | Google Cloud Run | Auto-generated |
| **Development** | develop | Local artifacts | http://localhost:8501 |
| **Demo** | main | Demo Cloud Run | Auto-generated |
| **Manual** | Any | Configurable | Configurable |

## 🛡️ Security Features

### Secret Management
- **No Hardcoded Secrets**: All secrets use environment variables
- **Secret Scanning**: Automated detection of exposed credentials
- **Template Exclusions**: Template files excluded from scanning
- **Masked Variables**: Sensitive data masked in logs

### Security Scanning
- **TruffleHog OSS**: Industry-standard secret detection
- **Custom Patterns**: Project-specific secret patterns
- **File Exclusions**: Template and example files excluded
- **GitLab Integration**: Built-in secret detection

## 📊 Pipeline Status

### Success Criteria
- ✅ Security scan passes
- ✅ Code quality checks pass
- ✅ All tests pass
- ✅ Docker images build successfully
- ✅ Deployment completes without errors

### Failure Handling
- **Security Failures**: Pipeline stops, requires manual review
- **Quality Failures**: Pipeline stops, requires code fixes
- **Test Failures**: Pipeline stops, requires bug fixes
- **Deployment Failures**: Rollback available, manual intervention

## 🔍 Troubleshooting

### Common Issues

#### 1. Missing Secrets
```bash
# Check if secrets are set
# GitHub: Settings > Secrets and Variables > Actions
# GitLab: Settings > CI/CD > Variables
```

#### 2. Docker Build Failures
```bash
# Check Dockerfile syntax
# Verify all dependencies in requirements.txt
# Test locally: docker build -t test .
```

#### 3. Deployment Failures
```bash
# Check GCP service account permissions
# Verify project ID and region
# Check Cloud Run quotas and limits
```

#### 4. Secret Detection False Positives
```bash
# Add exclusions to secret-detection-ruleset.toml
# Use template files for examples
# Avoid hardcoded values in production code
```

### Debug Commands

#### GitHub Actions
```bash
# Enable debug logging
echo "ACTIONS_STEP_DEBUG=true" >> $GITHUB_ENV
echo "ACTIONS_RUNNER_DEBUG=true" >> $GITHUB_ENV
```

#### GitLab CI/CD
```bash
# Enable debug logging
export CI_DEBUG_TRACE=true
```

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitLab CI/CD Documentation](https://docs.gitlab.com/ee/ci/)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Docker Documentation](https://docs.docker.com/)

## 🆘 Support

If you encounter issues with the CI/CD pipelines:

1. **Check the logs** in the respective platform
2. **Verify secrets** are properly configured
3. **Test locally** using the same commands
4. **Review security scans** for false positives
5. **Check GCP permissions** and quotas

---

**Remember**: Always test changes in development before deploying to production! 🚀
