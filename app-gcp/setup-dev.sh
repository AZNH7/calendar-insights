#!/bin/bash

# 🧪 Calendar Insights - App-GCP Development Environment Setup
# This script sets up a complete local development environment for the GCP application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="calendar-insights-gcp"
CONTAINER_NAME="calendar-insights-gcp-dev"
PORT=8080

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is available
is_port_available() {
    ! lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null
}

# Function to cleanup existing containers
cleanup_existing() {
    print_status "Cleaning up existing containers..."
    
    # Stop and remove existing container
    if docker ps -a --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_status "Stopping existing container: ${CONTAINER_NAME}"
        docker stop "${CONTAINER_NAME}" >/dev/null 2>&1 || true
        docker rm "${CONTAINER_NAME}" >/dev/null 2>&1 || true
    fi
    
    # Stop docker-compose if running
    if [ -f "${SCRIPT_DIR}/docker-compose.yml" ]; then
        print_status "Stopping docker-compose services..."
        cd "${SCRIPT_DIR}"
        docker-compose down >/dev/null 2>&1 || true
    fi
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p "${SCRIPT_DIR}/credentials"
    mkdir -p "${SCRIPT_DIR}/config"
    mkdir -p "${SCRIPT_DIR}/logs"
    mkdir -p "${SCRIPT_DIR}/data"
    
    print_success "Directories created"
}

# Function to create .env file
create_env_file() {
    local env_file="${SCRIPT_DIR}/.env"
    
    if [ ! -f "$env_file" ]; then
        print_status "Creating .env file..."
        
        cat > "$env_file" << EOF
# Calendar Insights - App-GCP Development Environment
# Generated on $(date)

# Application Configuration
PORT=8080
ENVIRONMENT=development
DEBUG=true

# Database Configuration for local PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=calendar_insights
POSTGRES_USER=dev_user
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-dev_password}

# Google Cloud Configuration (optional for local development)
# Uncomment and configure if you need GCP services
# GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account.json
# GOOGLE_CLOUD_PROJECT=your-project-id

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8080
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Development Settings
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1

# Custom Environment Variables
# Add your custom variables here
EOF
        
        print_success ".env file created at $env_file"
        print_warning "Please review and customize the .env file as needed"
    else
        print_status ".env file already exists, skipping creation"
    fi
}

# Function to create sample service account placeholder
create_service_account_placeholder() {
    local credentials_dir="${SCRIPT_DIR}/credentials"
    local sample_file="${credentials_dir}/README.md"
    
    if [ ! -f "$sample_file" ]; then
        print_status "Creating service account placeholder..."
        
        cat > "$sample_file" << EOF
# Service Account Credentials

This directory is for Google Cloud service account credentials.

## Setup Instructions

1. **Download your service account key:**
   - Go to Google Cloud Console
   - Navigate to IAM & Admin > Service Accounts
   - Find your service account
   - Click "Actions" > "Create Key"
   - Choose JSON format
   - Download the file

2. **Place the JSON file here:**
   \`\`\`bash
   cp /path/to/your/service-account-key.json ./service-account.json
   \`\`\`

3. **Update your .env file:**
   \`\`\`bash
   GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account.json
   \`\`\`

## Security Notes

- Never commit service account keys to version control
- The credentials directory is in .gitignore
- Use different service accounts for different environments
- Regularly rotate your service account keys

## Local Development

For local development without GCP services, you can skip this step.
The application will work in development mode without authentication.
EOF
        
        print_success "Service account placeholder created"
    fi
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    local missing_deps=()
    
    # Check Docker
    if ! command_exists docker; then
        missing_deps+=("docker")
    else
        # Check if Docker daemon is running
        if ! docker info >/dev/null 2>&1; then
            print_error "Docker is installed but not running. Please start Docker and try again."
            exit 1
        fi
    fi
    
    # Check Docker Compose
    if ! command_exists docker-compose; then
        missing_deps+=("docker-compose")
    fi
    
    # Check curl (for health checks)
    if ! command_exists curl; then
        missing_deps+=("curl")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing required dependencies: ${missing_deps[*]}"
        echo ""
        echo "Please install the missing dependencies:"
        echo "  Ubuntu/Debian: sudo apt-get install ${missing_deps[*]}"
        echo "  macOS: brew install ${missing_deps[*]}"
        echo "  Or visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    print_success "All prerequisites are installed"
}

# Function to check port availability
check_port() {
    if ! is_port_available $PORT; then
        print_warning "Port $PORT is already in use"
        print_status "Processes using port $PORT:"
        lsof -i :$PORT || true
        echo ""
        read -p "Do you want to continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_error "Setup cancelled. Please free port $PORT and try again."
            exit 1
        fi
    fi
}

# Function to build Docker image
build_image() {
    print_status "Building Docker image..."
    
    cd "${SCRIPT_DIR}"
    
    # Build the image
    docker build -t "${PROJECT_NAME}:dev" . || {
        print_error "Failed to build Docker image"
        exit 1
    }
    
    print_success "Docker image built successfully"
}

# Function to start the development environment
start_dev_environment() {
    print_status "Starting development environment..."
    
    cd "${SCRIPT_DIR}"
    
    # Start with docker-compose
    if [ -f "docker-compose.yml" ]; then
        print_status "Using docker-compose to start services..."
        docker-compose up -d || {
            print_error "Failed to start services with docker-compose"
            exit 1
        }
    else
        print_status "Starting container directly..."
        docker run -d \
            --name "${CONTAINER_NAME}" \
            -p ${PORT}:${PORT} \
            --env-file .env \
            -v "${SCRIPT_DIR}/credentials:/app/credentials:ro" \
            -v "${SCRIPT_DIR}/config:/app/config:ro" \
            -v "${SCRIPT_DIR}/logs:/app/logs" \
            -v "${SCRIPT_DIR}/data:/app/data" \
            "${PROJECT_NAME}:dev" || {
            print_error "Failed to start container"
            exit 1
        }
    fi
    
    print_success "Development environment started"
}

# Function to wait for application to be ready
wait_for_app() {
    print_status "Waiting for application to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://localhost:${PORT}/_stcore/health" >/dev/null 2>&1; then
            print_success "Application is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    echo ""
    print_warning "Application health check timed out, but it might still be starting..."
    return 1
}

# Function to show logs
show_logs() {
    print_status "Recent application logs:"
    echo "----------------------------------------"
    
    if [ -f "${SCRIPT_DIR}/docker-compose.yml" ]; then
        cd "${SCRIPT_DIR}"
        docker-compose logs --tail=20 app-gcp 2>/dev/null || docker-compose logs --tail=20
    else
        docker logs "${CONTAINER_NAME}" --tail=20 2>/dev/null || true
    fi
    
    echo "----------------------------------------"
}

# Function to generate test data
generate_test_data() {
    print_status "Generating test data..."
    
    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    sleep 10
    
    # Check if test data generator exists
    if [ ! -f "${SCRIPT_DIR}/generate-test-data.py" ]; then
        print_warning "Test data generator not found, skipping test data generation"
        return
    fi
    
    # Generate test data
    if docker-compose exec -T app-gcp python generate-test-data.py --users 50 --days 30 --meetings-per-day 25 --yes 2>/dev/null; then
        print_success "Test data generated successfully!"
    else
        print_warning "Failed to generate test data automatically"
        print_status "You can generate test data manually by running:"
        print_status "  docker-compose exec app-gcp python generate-test-data.py"
    fi
}

# Function to display final instructions
show_final_instructions() {
    echo ""
    echo "🎉 Development environment setup complete!"
    echo ""
    echo "📊 Access your application:"
    echo "   🌐 Web Interface: http://localhost:${PORT}"
    echo "   📱 Mobile friendly: http://$(hostname -I | awk '{print $1}'):${PORT}"
    echo ""
    echo "🛠️  Development commands:"
    echo "   📋 View logs:        docker-compose logs -f"
    echo "   🔄 Restart:          docker-compose restart"
    echo "   🛑 Stop:             docker-compose down"
    echo "   🔨 Rebuild:          docker-compose build && docker-compose up -d"
    echo "   🎲 Generate data:    ./setup-dev.sh test-data"
    echo ""
    echo "📁 Important directories:"
    echo "   🔐 Credentials:      ${SCRIPT_DIR}/credentials/"
    echo "   ⚙️  Configuration:   ${SCRIPT_DIR}/config/"
    echo "   📝 Logs:             ${SCRIPT_DIR}/logs/"
    echo "   💾 Data:             ${SCRIPT_DIR}/data/"
    echo ""
    echo "📖 Documentation:"
    echo "   📚 Development Guide: ${SCRIPT_DIR}/LOCAL_DEVELOPMENT.md"
    echo "   🔧 Environment File:  ${SCRIPT_DIR}/.env"
    echo ""
    echo "🆘 Troubleshooting:"
    echo "   🐛 If app doesn't load: docker-compose logs -f"
    echo "   🔄 If port conflicts:   Edit PORT in .env file"
    echo "   🧹 Clean restart:       docker-compose down && docker-compose up -d"
    echo ""
}

# Function to handle script interruption
cleanup_on_exit() {
    echo ""
    print_warning "Setup interrupted. Cleaning up..."
    cleanup_existing
    exit 1
}

# Main function
main() {
    echo "🚀 Calendar Insights - App-GCP Development Environment Setup"
    echo "============================================================"
    echo ""
    
    # Handle interruption
    trap cleanup_on_exit INT TERM
    
    # Change to script directory
    cd "${SCRIPT_DIR}"
    
    # Run setup steps
    check_prerequisites
    check_port
    cleanup_existing
    create_directories
    create_env_file
    create_service_account_placeholder
    build_image
    start_dev_environment
    
    # Wait for app and show status
    if wait_for_app; then
        show_logs
        
        # Generate test data
        echo ""
        read -p "🎲 Generate test data for easier testing? (Y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            generate_test_data
        fi
    fi
    
    show_final_instructions
}

# Parse command line arguments
case "${1:-}" in
    "clean")
        print_status "Cleaning up development environment..."
        cleanup_existing
        docker rmi "${PROJECT_NAME}:dev" 2>/dev/null || true
        print_success "Cleanup complete"
        exit 0
        ;;
    "logs")
        show_logs
        exit 0
        ;;
    "restart")
        print_status "Restarting development environment..."
        cleanup_existing
        start_dev_environment
        wait_for_app
        print_success "Restart complete"
        exit 0
        ;;
    "test-data")
        print_status "Generating test data..."
        if [ -f "${SCRIPT_DIR}/generate-test-data.py" ]; then
            cd "${SCRIPT_DIR}"
            if docker-compose exec app-gcp python generate-test-data.py --users 100 --days 60 --meetings-per-day 40; then
                print_success "Test data generation complete"
            else
                print_error "Test data generation failed"
                exit 1
            fi
        else
            print_error "Test data generator not found"
            exit 1
        fi
        exit 0
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  setup (default)  Set up the development environment"
        echo "  clean           Clean up containers and images"
        echo "  logs            Show application logs"
        echo "  restart         Restart the development environment"
        echo "  test-data       Generate realistic test data"
        echo "  help            Show this help message"
        exit 0
        ;;
    "")
        # Default: run setup
        main
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac
