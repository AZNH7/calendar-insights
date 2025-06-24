# Credentials Directory

⚠️ **SECURITY WARNING: This directory contains sensitive authentication files that should NEVER be committed to git.**

## Files in this directory:

### 🔐 Authentication Files (DO NOT COMMIT)
- `service-account.json` - Google Cloud service account credentials
- `token.json` - OAuth2 access and refresh tokens
- `oauth2_calendar_service.py` - OAuth2 authentication helper

### 📝 Template Files (Safe to commit)
- `service-account.json.template` - Template showing expected structure
- `README.md` - This file

## Setup Instructions:

1. **For Service Account Authentication:**
   ```bash
   cp service-account.json.template service-account.json
   # Edit service-account.json with your real credentials
   ```

2. **For OAuth2 Authentication:**
   - The `token.json` file is automatically created during OAuth flow
   - Never commit this file as it contains access tokens

## Security Best Practices:

✅ **DO:**
- Use environment variables for production deployments
- Store credentials in GCP Secret Manager
- Use `.template` files as examples
- Add all credential files to `.gitignore`

❌ **DON'T:**
- Commit real credentials to git
- Share credential files via email/chat
- Store credentials in code files
- Push credential files to remote repositories

## Production Deployment:

For production deployments, credentials should be:
1. Stored in GCP Secret Manager
2. Mounted as environment variables
3. Never stored in the container image 