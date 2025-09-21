#!/bin/bash

# 🎲 Quick Test Data Generator for Calendar Insights
# Simple wrapper around the Python test data generator

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if docker-compose is running
check_services() {
    cd "${SCRIPT_DIR}"
    if ! docker-compose ps | grep -q "Up"; then
        print_error "Development environment is not running!"
        print_status "Please start it first with: ./setup-dev.sh"
        exit 1
    fi
}

# Generate test data
generate_data() {
    local users=${1:-100}
    local days=${2:-60}
    local meetings_per_day=${3:-40}
    
    print_status "Generating test data..."
    print_status "  👥 Users: ${users}"
    print_status "  📅 Days of history: ${days}"
    print_status "  📊 Meetings per day: ${meetings_per_day}"
    
    cd "${SCRIPT_DIR}"
    
    if docker-compose exec app-gcp python generate-test-data.py \
        --users "${users}" \
        --days "${days}" \
        --meetings-per-day "${meetings_per_day}" \
        --yes; then
        print_success "Test data generated successfully!"
        echo ""
        print_status "🌐 Open http://localhost:8080 to see your data"
    else
        print_error "Failed to generate test data"
        exit 1
    fi
}

# Show database stats
show_stats() {
    print_status "Getting database statistics..."
    cd "${SCRIPT_DIR}"
    
    if docker-compose exec app-gcp python generate-test-data.py --stats-only; then
        print_success "Database statistics retrieved"
    else
        print_error "Failed to get database statistics"
        exit 1
    fi
}

# Clear all data
clear_data() {
    print_warning "This will delete ALL data from the database!"
    read -p "Are you sure? Type 'yes' to confirm: " -r
    if [[ $REPLY == "yes" ]]; then
        cd "${SCRIPT_DIR}"
        if docker-compose exec app-gcp python generate-test-data.py --clear --yes; then
            print_success "Database cleared successfully"
        else
            print_error "Failed to clear database"
            exit 1
        fi
    else
        print_status "Operation cancelled"
    fi
}

# Main function
main() {
    echo "🎲 Calendar Insights - Test Data Generator"
    echo "=========================================="
    
    check_services
    
    case "${1:-generate}" in
        "small")
            generate_data 25 14 15
            ;;
        "medium")
            generate_data 50 30 25
            ;;
        "large")
            generate_data 100 60 40
            ;;
        "xlarge")
            generate_data 200 90 60
            ;;
        "stats")
            show_stats
            ;;
        "clear")
            clear_data
            ;;
        "generate"|"")
            generate_data
            ;;
        "help"|"-h"|"--help")
            echo ""
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  generate (default)  Generate default test data (100 users, 60 days)"
            echo "  small              Generate small dataset (25 users, 14 days)"
            echo "  medium             Generate medium dataset (50 users, 30 days)"
            echo "  large              Generate large dataset (100 users, 60 days)"
            echo "  xlarge             Generate extra large dataset (200 users, 90 days)"
            echo "  stats              Show current database statistics"
            echo "  clear              Clear all data from database"
            echo "  help               Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                 # Generate default dataset"
            echo "  $0 small           # Quick test data for demos"
            echo "  $0 xlarge          # Comprehensive test data"
            echo "  $0 stats           # Check current data"
            ;;
        *)
            print_error "Unknown command: $1"
            echo "Run '$0 help' for usage information"
            exit 1
            ;;
    esac
}

main "$@"
