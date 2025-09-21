#!/bin/bash

# 🚀 Calendar Insights - Unified Deployment Script
# This single script handles all deployment scenarios: local, cloud, and AI setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Check if we're in the right directory
if [ ! -f "dashboard.py" ]; then
    log_error "Please run this script from the app-gcp directory"
    exit 1
fi

# Check for required tools
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_tools=()
    
    if ! command -v docker >/dev/null 2>&1; then
        missing_tools+=("docker")
    fi
    
    if ! command -v docker-compose >/dev/null 2>&1; then
        missing_tools+=("docker-compose")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_info "Please install the missing tools and try again"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Setup environment file
setup_environment() {
    if [ ! -f ".env" ]; then
        log_info "Creating environment file from template..."
        cp env.template .env
        log_warning "Please edit .env file with your configuration before continuing"
        log_info "Required: GOOGLE_CLOUD_PROJECT, POSTGRES_PASSWORD, GOOGLE_API_KEY"
        exit 1
    fi
    
    # Load environment variables
    source .env
    
    # Check required variables for local deployment
    if [ "$1" = "local" ] || [ -z "$1" ]; then
        local required_vars=("POSTGRES_PASSWORD")
        local missing_vars=()
        
        for var in "${required_vars[@]}"; do
            if [ -z "${!var}" ]; then
                missing_vars+=("$var")
            fi
        done
        
        if [ ${#missing_vars[@]} -ne 0 ]; then
            log_error "Missing required environment variables for local deployment:"
            printf '   - %s\n' "${missing_vars[@]}"
            log_info "Please set these in your .env file"
            log_info "Example: POSTGRES_PASSWORD=your-secure-password"
            exit 1
        fi
    fi
    
    log_success "Environment configuration verified"
}

# Local Docker deployment
deploy_local() {
    log_info "Setting up local Docker environment..."
    
    # Set environment variables (no defaults for security)
    export POSTGRES_PASSWORD="${POSTGRES_PASSWORD}"
    export GOOGLE_API_KEY="${GOOGLE_API_KEY:-}"
    
    log_info "Configuration:"
    log_info "   Database Password: ${POSTGRES_PASSWORD}"
    log_info "   Google API Key: ${GOOGLE_API_KEY:+SET}"
    
    # Create necessary directories
    log_info "Creating directories..."
    mkdir -p logs config credentials
    
    # Stop any existing containers
    log_info "Stopping existing containers..."
    docker-compose down 2>/dev/null || true
    
    # Build and start the services
    log_info "Building and starting services..."
    docker-compose up -d --build
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 10
    
    # Check if services are running
    log_info "Checking service status..."
    if docker-compose ps | grep -q "Up"; then
        log_success "Services are running"
    else
        log_error "Services failed to start. Check logs with: docker-compose logs"
        exit 1
    fi
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose exec -T postgres pg_isready -U dev_user -d calendar_insights > /dev/null 2>&1; then
            log_success "Database is ready"
            break
        fi
        
        attempt=$((attempt + 1))
        log_info "   Attempt $attempt/$max_attempts - waiting for database..."
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        log_error "Database failed to start within expected time"
        exit 1
    fi
    
    # Initialize database and generate test data
    log_info "Initializing database and generating test data..."
    docker-compose exec app-gcp python generate_test_data.py
    
    log_success "Local development environment ready!"
    echo ""
    log_info "🌐 Access your application:"
    log_info "   Dashboard: http://localhost:8080"
    log_info "   AI Chat: http://localhost:8080 (click '🤖 AI Chat Assistant')"
    echo ""
    log_info "🔧 Useful Commands:"
    log_info "   View logs: docker-compose logs -f"
    log_info "   Stop services: docker-compose down"
    log_info "   Restart services: docker-compose restart"
}

# Cloud deployment
deploy_cloud() {
    log_info "Deploying to Google Cloud Run..."
    
    # Check for gcloud
    if ! command -v gcloud >/dev/null 2>&1; then
        log_error "gcloud CLI is required for cloud deployment"
        log_info "Please install it from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    # Check for required cloud variables
    local cloud_vars=("GOOGLE_CLOUD_PROJECT")
    local missing_cloud_vars=()
    
    for var in "${cloud_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_cloud_vars+=("$var")
        fi
    done
    
    if [ ${#missing_cloud_vars[@]} -ne 0 ]; then
        log_error "Missing required cloud environment variables:"
        printf '   - %s\n' "${missing_cloud_vars[@]}"
        log_info "Please set these in your .env file for cloud deployment"
        exit 1
    fi
    
    # Run the cloud deployment script
    if [ -f "scripts/cloud-deploy.sh" ]; then
        log_info "Running cloud deployment script..."
        ./scripts/cloud-deploy.sh
    else
        log_error "Cloud deployment script not found"
        log_info "Please ensure scripts/cloud-deploy.sh exists"
        exit 1
    fi
}

# AI Chat setup
setup_ai() {
    log_info "Setting up AI Chat Assistant..."
    
    # Check for gcloud
    if ! command -v gcloud >/dev/null 2>&1; then
        log_error "gcloud CLI is required for AI setup"
        log_info "Please install it from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    # Get project ID
    local project_id="${GOOGLE_CLOUD_PROJECT:-${GCP_PROJECT_ID}}"
    if [ -z "$project_id" ]; then
        log_error "GOOGLE_CLOUD_PROJECT or GCP_PROJECT_ID environment variable must be set"
        exit 1
    fi
    
    log_info "Project ID: ${project_id}"
    
    # Check if API key secret exists
    log_info "Checking for existing Google API key..."
    if gcloud secrets describe google_api_key --project=$project_id &> /dev/null; then
        log_success "Google API key secret already exists"
        read -p "Do you want to update it? (y/N): " update_key
        if [[ ! $update_key =~ ^[Yy]$ ]]; then
            log_info "Skipping API key setup"
            return 0
        fi
    else
        log_warning "Google API key secret not found"
        update_key=true
    fi
    
    if [ "$update_key" = true ]; then
        echo ""
        log_info "🔑 Setting up Google API Key for AI Chat"
        echo "========================================"
        echo ""
        log_info "To use the AI chat feature, you need a Google API key with access to:"
        log_info "• Generative AI API (Gemini)"
        echo ""
        log_info "Steps to get your API key:"
        log_info "1. Go to: https://aistudio.google.com/app/apikey"
        log_info "2. Click 'Create API Key'"
        log_info "3. Copy the generated API key"
        echo ""
        
        read -p "Enter your Google API key: " -s api_key
        echo ""
        
        if [ -z "$api_key" ]; then
            log_error "API key cannot be empty"
            exit 1
        fi
        
        # Validate API key format (basic check)
        if [[ ! $api_key =~ ^AIza[0-9A-Za-z_-]{35}$ ]]; then
            log_warning "API key format doesn't look like a standard Google API key"
            read -p "Continue anyway? (y/N): " continue_anyway
            if [[ ! $continue_anyway =~ ^[Yy]$ ]]; then
                log_info "Setup cancelled"
                exit 1
            fi
        fi
        
        # Create or update the secret
        log_info "Storing API key in Google Secret Manager..."
        echo "$api_key" | gcloud secrets create google_api_key \
            --data-file=- \
            --project=$project_id \
            2>/dev/null || echo "$api_key" | gcloud secrets versions add google_api_key \
            --data-file=- \
            --project=$project_id
        
        log_success "Google API key stored successfully!"
    fi
    
    log_success "AI Chat setup complete!"
    echo ""
    log_info "Next steps:"
    log_info "1. Deploy your application: ./deploy.sh cloud"
    log_info "2. Access the AI chat from the dashboard"
    log_info "3. Try asking questions about your meeting data"
}

# Main deployment logic
main() {
    echo "🚀 Calendar Insights - Unified Deployment"
    echo "=========================================="
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Setup environment
    setup_environment
    
    # Parse command line arguments
    local deployment_type=""
    if [ $# -eq 0 ]; then
        # Interactive mode
        echo "Choose deployment type:"
        echo "1) Local Docker (for development/testing)"
        echo "2) Google Cloud Run (for production)"
        echo "3) Setup AI Chat Assistant only"
        read -p "Enter your choice (1-3): " choice
        
        case $choice in
            1) deployment_type="local" ;;
            2) deployment_type="cloud" ;;
            3) deployment_type="ai" ;;
            *) log_error "Invalid choice. Please run the script again."; exit 1 ;;
        esac
    else
        deployment_type="$1"
    fi
    
    # Execute deployment
    case $deployment_type in
        "local")
            deploy_local
            ;;
        "cloud")
            deploy_cloud
            ;;
        "ai")
            setup_ai
            ;;
        *)
            log_error "Invalid deployment type: $deployment_type"
            log_info "Usage: $0 [local|cloud|ai]"
            log_info "  local  - Deploy with Docker Compose for development"
            log_info "  cloud  - Deploy to Google Cloud Run"
            log_info "  ai     - Setup AI Chat Assistant only"
            exit 1
            ;;
    esac
    
    echo ""
    log_success "Deployment completed successfully!"
    echo ""
    log_info "📖 Next steps:"
    log_info "   - Check the logs for any issues"
    log_info "   - Access your application at the provided URL"
    log_info "   - Configure your Google Calendar API credentials"
    echo ""
    log_info "📚 Documentation:"
    log_info "   - README.md - Full setup guide"
    log_info "   - LOCAL_DEVELOPMENT.md - Local development guide"
    log_info "   - AI_CHAT_FEATURE.md - AI Chat Assistant guide"
}

# Run main function
main "$@"