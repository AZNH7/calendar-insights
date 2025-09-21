#!/bin/bash

# 🚀 Calendar Insights - Quick GCP App Development Setup
# Wrapper script to setup the app-gcp development environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_GCP_DIR="${SCRIPT_DIR}/app-gcp"

# Check if app-gcp directory exists
if [ ! -d "$APP_GCP_DIR" ]; then
    echo "❌ Error: app-gcp directory not found at $APP_GCP_DIR"
    exit 1
fi

# Check if setup script exists
if [ ! -f "$APP_GCP_DIR/setup-dev.sh" ]; then
    echo "❌ Error: setup-dev.sh not found in app-gcp directory"
    exit 1
fi

# Run the actual setup script
echo "🚀 Starting Calendar Insights GCP App development setup..."
echo "📁 Working directory: $APP_GCP_DIR"
echo ""

cd "$APP_GCP_DIR"
exec "./setup-dev.sh" "$@"
