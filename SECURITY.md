# 🔒 Security Guide

This document outlines security best practices for Calendar Insights deployment and configuration.

## 🚨 Critical Security Requirements

### 1. Environment Variables & Secrets

**NEVER commit sensitive data to version control:**

- ❌ `.env` files
- ❌ Service account keys
- ❌ API keys
- ❌ Database passwords
- ❌ OAuth secrets

**✅ Use secure methods:**

- Environment variables in CI/CD
- Google Secret Manager (production)
- Local `.env` files (development only)

### 2. Required Secrets

#### For Local Development:
```bash
# Required
POSTGRES_PASSWORD=your-secure-password

# Optional
GOOGLE_API_KEY=your-google-ai-api-key
GOOGLE_CLIENT_ID=your-oauth-client-id
GOOGLE_CLIENT_SECRET=your-oauth-client-secret
SECRET_KEY=your-app-secret-key
```

#### For Production (CI/CD):
```bash
# GitHub Actions Secrets / GitLab CI Variables
GOOGLE_CLOUD_PROJECT=your-project-id
POSTGRES_PASSWORD=your-secure-password
GOOGLE_CLIENT_SECRET=your-oauth-client-secret
SECRET_KEY=your-app-secret-key
GOOGLE_API_KEY=your-google-ai-api-key
```

### 3. Password Generation

**Generate strong passwords:**

```bash
# Generate secure password (32 characters)
openssl rand -base64 32

# Generate secure password (16 characters, URL-safe)
openssl rand -base64 32 | tr -d "=+/" | cut -c1-16
```

**Password requirements:**
- Minimum 16 characters
- Mix of uppercase, lowercase, numbers, symbols
- Unique for each environment
- Rotated regularly

## 🛡️ Security Best Practices

### 1. Local Development

```bash
# 1. Copy environment template
cp env.local.example .env

# 2. Set secure passwords
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32)" >> .env

# 3. Never commit .env
echo ".env" >> .gitignore
```

### 2. Production Deployment

```bash
# 1. Use Google Secret Manager
gcloud secrets create postgres_password --data-file=- <<< "your-secure-password"

# 2. Set CI/CD secrets
# GitHub: Settings > Secrets and Variables > Actions
# GitLab: Settings > CI/CD > Variables
```

### 3. Service Account Security

```bash
# 1. Create dedicated service account
gcloud iam service-accounts create calendar-insights-sa

# 2. Grant minimal required permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:calendar-insights-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"

# 3. Download key securely
gcloud iam service-accounts keys create key.json \
  --iam-account=calendar-insights-sa@PROJECT_ID.iam.gserviceaccount.com
```

## 🔍 Security Checklist

### Before Deployment:
- [ ] All secrets are in environment variables
- [ ] No hardcoded passwords in code
- [ ] Strong passwords generated
- [ ] Service account has minimal permissions
- [ ] Secrets are masked in CI/CD logs
- [ ] `.env` files are in `.gitignore`

### After Deployment:
- [ ] Test with production secrets
- [ ] Verify no secrets in logs
- [ ] Check database access controls
- [ ] Validate API key permissions
- [ ] Monitor for security alerts

## 🚨 Common Security Issues

### 1. Hardcoded Passwords
```bash
# ❌ BAD
POSTGRES_PASSWORD=dev_password

# ✅ GOOD
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
```

### 2. Default Passwords
```bash
# ❌ BAD
POSTGRES_PASSWORD=password123

# ✅ GOOD
POSTGRES_PASSWORD=your-secure-generated-password
```

### 3. Exposed API Keys
```bash
# ❌ BAD - in code
api_key = "AIzaSyA3wpBzdpVjaZqkyMdXI34VyORw0l5Ym1A"

# ✅ GOOD - in environment
api_key = os.getenv('GOOGLE_API_KEY')
```

## 🔧 Security Tools

### 1. Secret Scanning
```bash
# Scan for hardcoded secrets
grep -r "password\|secret\|key" --include="*.py" --include="*.sh" .

# Check for exposed credentials
git log --all --full-history -- "*.env" "*.key" "*.json"
```

### 2. Environment Validation
```bash
# Validate required secrets are set
python3 -c "
import os
required = ['POSTGRES_PASSWORD']
missing = [var for var in required if not os.getenv(var)]
if missing:
    print(f'Missing: {missing}')
    exit(1)
print('All required secrets are set')
"
```

## 📞 Security Incident Response

### If Secrets Are Compromised:

1. **Immediately rotate all affected secrets**
2. **Revoke compromised API keys**
3. **Update service account keys**
4. **Audit access logs**
5. **Notify team members**

### Emergency Commands:
```bash
# Rotate database password
gcloud sql users set-password calendar_user \
  --instance=calendar-insights-db \
  --password="$(openssl rand -base64 32)"

# Revoke API key
# (Do this in Google Cloud Console)

# Regenerate service account key
gcloud iam service-accounts keys create new-key.json \
  --iam-account=calendar-insights-sa@PROJECT_ID.iam.gserviceaccount.com
```

## 📚 Additional Resources

- [Google Cloud Security Best Practices](https://cloud.google.com/security/best-practices)
- [OWASP Secrets Management](https://owasp.org/www-project-secrets-management/)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security/security-advisories)
- [GitLab Security](https://docs.gitlab.com/ee/security/)

---

**Remember: Security is everyone's responsibility. When in doubt, ask for help!**
