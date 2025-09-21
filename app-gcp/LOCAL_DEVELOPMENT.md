# 🧪 Local Development Guide for App-GCP

This guide helps you test the GCP application locally before deploying to Google Cloud Run.

## 🚀 Quick Start

### Option 1: Using Setup Script (Easiest)

```bash
# From project root
./setup-dev-gcp.sh

# Or from app-gcp directory
cd app-gcp
./setup-dev.sh
```

The setup script will:
- Check all prerequisites
- Create necessary directories and files
- Build the Docker image
- Start the development environment
- Provide detailed instructions

### Option 2: Using Docker Compose (Manual)

```bash
# Navigate to app-gcp directory
cd app-gcp

# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Access the application
open http://localhost:8080

# Stop the application
docker-compose down
```

### Option 2: Using Docker directly

```bash
# Navigate to app-gcp directory
cd app-gcp

# Build the image
docker build -t calendar-insights-gcp:local .

# Run the container
docker run -d \
  --name calendar-insights-gcp \
  -p 8080:8080 \
  -e ENVIRONMENT=development \
  -e DEBUG=true \
  calendar-insights-gcp:local

# View logs
docker logs calendar-insights-gcp -f

# Stop and remove
docker stop calendar-insights-gcp && docker rm calendar-insights-gcp
```

### Option 3: Setup Script Commands

The setup script supports multiple commands:

```bash
# Default setup
./setup-dev.sh

# View logs
./setup-dev.sh logs

# Restart environment
./setup-dev.sh restart

# Clean up everything
./setup-dev.sh clean

# Show help
./setup-dev.sh help
```

## 🔧 Configuration

### Automated Setup

The `setup-dev.sh` script automatically creates all necessary configuration files:

- `.env` - Environment variables
- `credentials/README.md` - Service account setup guide
- Required directories (`credentials/`, `config/`, `logs/`, `data/`)

### Environment Variables

The setup script creates a `.env` file, or you can create one manually:

```bash
# .env
PORT=8080
ENVIRONMENT=development
DEBUG=true

# Google Cloud credentials (optional for local testing)
# GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account.json

# Database connection (if using local database)
# Set your database connection string here
# Use environment variables for credentials
```

### Service Account (Optional)

For full GCP integration testing:

1. Download your service account JSON file
2. Place it in `app-gcp/credentials/service-account.json`
3. Uncomment the `GOOGLE_APPLICATION_CREDENTIALS` environment variable

## 🧪 Testing Features

### Test Data Generation

Generate realistic fake data for testing:

```bash
# Quick and easy - use the wrapper script
./generate-data.sh

# Different dataset sizes
./generate-data.sh small    # 25 users, 14 days
./generate-data.sh medium   # 50 users, 30 days  
./generate-data.sh large    # 100 users, 60 days
./generate-data.sh xlarge   # 200 users, 90 days

# Check current database stats
./generate-data.sh stats

# Clear all data
./generate-data.sh clear

# Or use the Python script directly with custom parameters
docker-compose exec app-gcp python generate-test-data.py --users 150 --days 45 --meetings-per-day 35
```

The test data includes:
- **Realistic users** across multiple departments (Engineering, Marketing, Sales, etc.)
- **Varied meeting types** (standups, reviews, 1:1s, all-hands, etc.)
- **Business hours bias** with some after-hours meetings
- **Department clustering** - most meetings within same department
- **Manager/IC distribution** - realistic management hierarchy
- **External attendees** - clients, vendors, contractors
- **Meeting acceptance rates** - realistic response patterns

### Health Check

```bash
curl http://localhost:8080/_stcore/health
```

### API Endpoints

Test your Streamlit application by navigating to:
- Main dashboard: http://localhost:8080
- Admin interface: http://localhost:8080 (if available)

### Logs

Monitor application logs:

```bash
# Docker Compose
docker-compose logs -f app-gcp

# Docker
docker logs calendar-insights-gcp -f
```

## 🔄 Development Workflow

1. **Make changes** to your application code
2. **Rebuild** the Docker image:
   ```bash
   docker-compose build
   ```
3. **Restart** the container:
   ```bash
   docker-compose up -d
   ```
4. **Test** your changes at http://localhost:8080
5. **Check logs** for any issues
6. **Commit** and push when ready

## 🐛 Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs app-gcp

# Check if port is already in use
lsof -i :8080

# Rebuild without cache
docker-compose build --no-cache
```

### Permission issues with volumes

```bash
# Fix permissions for mounted directories
sudo chown -R $USER:$USER ./credentials ./config ./logs
```

### Database connection issues

1. Ensure database service is running (if using local PostgreSQL)
2. Check connection string
3. Verify credentials

## 📊 Performance Testing

### Load Testing

```bash
# Install apache bench
sudo apt-get install apache2-utils

# Test basic load
ab -n 100 -c 10 http://localhost:8080/

# Test specific endpoint
ab -n 50 -c 5 http://localhost:8080/_stcore/health
```

### Memory Usage

```bash
# Monitor container resources
docker stats calendar-insights-gcp

# Or with docker-compose
docker-compose top
```

## 🚀 Production Readiness Checklist

Before deploying to GCP:

- [ ] Application starts without errors
- [ ] Health check endpoint responds
- [ ] All environment variables are properly configured
- [ ] Service account authentication works (if required)
- [ ] Database connections are stable
- [ ] No sensitive data in logs
- [ ] Application handles errors gracefully
- [ ] Performance is acceptable under load

## 💡 Tips

1. **Use docker-compose** for easier development
2. **Mount volumes** for live code reloading during development
3. **Test with realistic data** to catch edge cases
4. **Monitor logs** continuously during testing
5. **Use environment variables** for configuration differences

## 🔗 Related Files

- `Dockerfile` - Container definition
- `docker-compose.yml` - Local development setup
- `requirements.txt` - Python dependencies
- `.env` - Environment variables (create this file)
- `credentials/` - Service account files (create this directory)
