# Calendar Insights

A Python application for analyzing and visualizing calendar data, integrating with Google Calendar API, Okta, and AWS services.

## Features

- Google Calendar API integration
- Okta authentication
- AWS service integration
- Data visualization using Streamlit
- Automated data processing with cron jobs
- PostgreSQL database integration
- Docker containerization
- Supervisor process management

## Prerequisites

- Python 3.8+
- PostgreSQL database
- Google Cloud Platform account with Calendar API enabled
- Okta account
- AWS account
- Docker and Docker Compose (for containerized deployment)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/calendar-insights.git
cd calendar-insights
```

2. Install dependencies:
```bash
cd app
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.template .env
```
Edit the `.env` file with your configuration details.

## Configuration

The application requires the following environment variables:

### Google API Configuration
- `SERVICE_ACCOUNT_FILE`: Path to your Google service account JSON file
- `DELEGATED_USER`: Email of the delegated user
- `GSUITE_DELEGATED_USER`: GSuite delegated user email

### Okta Configuration
- `OKTA_DOMAIN`: Your Okta domain
- `OKTA_API_TOKEN`: Okta API token

### Database Configuration
- `DB_HOST`: Database host
- `DB_PORT`: Database port
- `DB_NAME`: Database name
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password

### AWS Configuration
- `AWS_REGION`: AWS region
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key

## Project Structure

```
app/
├── config/           # Configuration files
├── credentials/      # Service account and authentication files
├── db/              # Database related files
├── .env.template    # Environment variables template
├── crontab          # Cron job configurations
├── docker-compose.yml # Docker Compose configuration
├── Dockerfile       # Docker container configuration
├── entrypoint.sh    # Container entrypoint script
├── init_db.py       # Database initialization script
├── requirements.txt # Python dependencies
├── supervisord.conf # Supervisor process configuration
└── test-cron.sh     # Test cron job script
```

## Scheduled Jobs

The application uses cron jobs for automated data processing:

- Main job: Runs daily at 1 AM UTC (loads JSON data)
- Test job: Runs every 5 minutes (for monitoring)

## Dependencies

- google-auth-oauthlib >= 0.4.6
- google-api-python-client >= 2.0.0
- numpy == 1.24.3
- pandas == 2.0.3
- requests >= 2.26.0
- python-dotenv == 1.0.0
- boto3 >= 1.26.0
- botocore >= 1.29.0
- psycopg2-binary == 2.9.9
- streamlit == 1.29.0
- plotly == 5.18.0
- sqlalchemy == 2.0.23
- ijson == 3.2.3
- PyYAML == 6.0.1
- altair == 5.1.0

## Docker Deployment

The application can be deployed using Docker:

```bash
docker-compose up -d
```

This will start the application with all necessary services and configurations.
