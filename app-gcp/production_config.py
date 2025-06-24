#!/usr/bin/env python3
"""
Production Configuration Manager for Calendar Insights
Handles environment-specific configuration for GCP deployment
"""

import os
import yaml
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductionConfig:
    """Production configuration manager"""
    
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            # Use local config directory when running locally, /app/config in container
            if os.path.exists('/app'):
                config_dir = "/app/config"
            else:
                config_dir = "./config"
        
        self.config_dir = Path(config_dir)
        self.environment = os.getenv('ENVIRONMENT', 'production')
        self._config_cache = {}
        
        # Only create config directory if we have write permissions
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError):
            logger.warning(f"Cannot create config directory: {self.config_dir}")
        
        logger.info(f"Initialized config manager for environment: {self.environment}")
    
    def get_database_config(self) -> Dict[str, Any]:
        """
        Get database configuration with environment variable precedence.
        All sensitive values must be provided via environment variables.
        """
        logger.info("🔧 Getting database configuration...")
        
        # Log available environment variables (without values for security)
        logger.info(f"DB_HOST env var: {'✓' if os.getenv('DB_HOST') else '✗'}")
        logger.info(f"POSTGRES_HOST env var: {'✓' if os.getenv('POSTGRES_HOST') else '✗'}")
        logger.info(f"POSTGRES_PORT env var: {'✓' if os.getenv('POSTGRES_PORT') else '✗'}")
        
        db_host_env = os.getenv('DB_HOST')
        postgres_host_env = os.getenv('POSTGRES_HOST')
        postgres_port_env = os.getenv('POSTGRES_PORT', '5432')
        
        # Validate that required host is provided
        if not db_host_env and not postgres_host_env:
            raise ValueError("Either DB_HOST or POSTGRES_HOST environment variable must be set")
        
        # DB_HOST takes precedence if set (e.g., for Cloud SQL proxy socket or specific host override)
        if db_host_env and db_host_env.startswith('/cloudsql/'): # Cloud SQL socket
            host = db_host_env
            port = None  # Unix socket doesn't use port
            parts = db_host_env.split('/')
            if len(parts) >= 3:
                # Extract project info for logging (without exposing full path)
                logger.info(f"Cloud SQL socket connection detected")
            else:
                logger.warning(f"Malformed Cloud SQL socket path. Falling back.")
                host = postgres_host_env
                port = int(postgres_port_env)
        elif db_host_env and db_host_env.startswith('/'): # Other Unix socket
            host = db_host_env
            port = None
            logger.info(f"Unix socket connection: {host}")
        elif db_host_env: # DB_HOST is a hostname (TCP/IP)
            host = db_host_env
            port = int(os.getenv('POSTGRES_PORT', '5432'))
            logger.info(f"TCP/IP connection with DB_HOST: {host}:{port}")
        else: # Fallback to POSTGRES_HOST for TCP/IP
            host = postgres_host_env
            port = int(postgres_port_env)
            logger.info(f"TCP/IP connection with POSTGRES_HOST: {host}:{port}")
        
        # Handle password retrieval: use environment variable
        password = os.getenv('POSTGRES_PASSWORD')
        if not password:
            raise ValueError("POSTGRES_PASSWORD environment variable must be set")
        logger.info("Using POSTGRES_PASSWORD environment variable for database password.")
        
        # Get other required database parameters
        db_name = os.getenv('POSTGRES_DB')
        db_user = os.getenv('POSTGRES_USER')
        
        if not db_name:
            raise ValueError("POSTGRES_DB environment variable must be set")
        if not db_user:
            raise ValueError("POSTGRES_USER environment variable must be set")
        
        db_config = {
            'type': os.getenv('DB_TYPE', 'postgres'),
            'host': host,
            'port': port,
            'database': db_name,
            'username': db_user,
            'password': password,
            'ssl_mode': os.getenv('DB_SSL_MODE', 'prefer'),
            'connection_timeout': int(os.getenv('DB_TIMEOUT_SECONDS', '30')),
            'pool_size': int(os.getenv('DB_POOL_SIZE', '5')),
            'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '10')),
        }
        
        # Add Google Cloud specific configuration if in GCP
        if os.getenv('GOOGLE_CLOUD_PROJECT'):
            db_config.update({
                'gcp_project': os.getenv('GOOGLE_CLOUD_PROJECT'),
                'cloud_sql_connection': os.getenv('CLOUD_SQL_CONNECTION_NAME')
            })
        
        return db_config
    
    def get_google_api_config(self) -> Dict[str, Any]:
        """Get Google API configuration from environment variables"""
        # Validate required Google API credentials
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        
        if not client_id:
            logger.warning("GOOGLE_CLIENT_ID not set - Google API features may not work")
        if not client_secret:
            logger.warning("GOOGLE_CLIENT_SECRET not set - Google API features may not work")
            
        return {
            'project_id': os.getenv('GOOGLE_CLOUD_PROJECT'),
            'client_id': client_id,
            'client_secret': client_secret,
            'credentials_file': os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '/app/credentials/service-account.json'),
            'scopes': [
                'https://www.googleapis.com/auth/calendar.readonly',
                'https://www.googleapis.com/auth/admin.directory.user.readonly'
            ],
            'rate_limits': {
                'requests_per_100_seconds': int(os.getenv('GOOGLE_API_RATE_LIMIT', '100')),
                'requests_per_day': int(os.getenv('GOOGLE_API_DAILY_LIMIT', '1000000'))
            }
        }
    
    def get_app_config(self) -> Dict[str, Any]:
        """Get application configuration"""
        return {
            'name': 'Calendar Insights',
            'version': os.getenv('APP_VERSION', '1.0.0'),
            'environment': self.environment,
            'debug': os.getenv('DEBUG', 'false').lower() == 'true',
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'port': int(os.getenv('PORT', '8501')),
            'host': os.getenv('HOST', '0.0.0.0'),
            'cache_ttl': int(os.getenv('CACHE_TTL_SECONDS', '300')),
            'max_file_size_mb': int(os.getenv('MAX_FILE_SIZE_MB', '50')),
            'default_fetch_days': int(os.getenv('DEFAULT_FETCH_DAYS', '30')),
            'cache_ttl_seconds': int(os.getenv('CACHE_TTL_SECONDS', '300')),
            'session_timeout_minutes': int(os.getenv('SESSION_TIMEOUT_MINUTES', '60')),
            'auto_refresh_enabled': os.getenv('AUTO_REFRESH_ENABLED', 'true').lower() == 'true'
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        secret_key = os.getenv('SECRET_KEY')
        if not secret_key:
            raise ValueError("SECRET_KEY environment variable must be set for security")
            
        return {
            'allowed_origins': os.getenv('ALLOWED_ORIGINS', '*').split(','),
            'secret_key': secret_key,
            'enable_auth': os.getenv('ENABLE_AUTH', 'false').lower() == 'true',
            'auth_provider': os.getenv('AUTH_PROVIDER', 'google'),
            'cors_enabled': os.getenv('CORS_ENABLED', 'true').lower() == 'true',
            'rate_limiting': {
                'enabled': os.getenv('RATE_LIMITING_ENABLED', 'true').lower() == 'true',
                'requests_per_minute': int(os.getenv('RATE_LIMIT_REQUESTS_PER_MINUTE', '60')),
                'burst_limit': int(os.getenv('RATE_LIMIT_BURST', '10'))
            }
        }
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring and logging configuration"""
        return {
            'enable_metrics': os.getenv('ENABLE_METRICS', 'true').lower() == 'true',
            'metrics_endpoint': os.getenv('METRICS_ENDPOINT', '/metrics'),
            'health_check_endpoint': os.getenv('HEALTH_CHECK_ENDPOINT', '/health'),
            'log_format': os.getenv('LOG_FORMAT', 'json'),
            'log_file': os.getenv('LOG_FILE', '/app/logs/application.log'),
            'structured_logging': os.getenv('STRUCTURED_LOGGING', 'true').lower() == 'true',
            'error_reporting': {
                'enabled': os.getenv('ERROR_REPORTING_ENABLED', 'true').lower() == 'true',
                'service_name': os.getenv('ERROR_REPORTING_SERVICE', 'calendar-insights'),
                'version': os.getenv('APP_VERSION', '1.0.0')
            },
            'performance_monitoring': {
                'enabled': os.getenv('PERFORMANCE_MONITORING_ENABLED', 'true').lower() == 'true',
                'sample_rate': float(os.getenv('PERFORMANCE_SAMPLE_RATE', '0.1'))
            }
        }
    
    def get_feature_flags(self) -> Dict[str, bool]:
        """Get feature flag configuration"""
        return {
            'enhanced_dashboard': os.getenv('FEATURE_ENHANCED_DASHBOARD', 'true').lower() == 'true',
            'real_time_updates': os.getenv('FEATURE_REAL_TIME_UPDATES', 'false').lower() == 'true',
            'data_export': os.getenv('FEATURE_DATA_EXPORT', 'true').lower() == 'true',
            'advanced_filters': os.getenv('FEATURE_ADVANCED_FILTERS', 'true').lower() == 'true',
            'meeting_insights': os.getenv('FEATURE_MEETING_INSIGHTS', 'true').lower() == 'true',
            'automated_reports': os.getenv('FEATURE_AUTOMATED_REPORTS', 'false').lower() == 'true',
            'api_access': os.getenv('FEATURE_API_ACCESS', 'false').lower() == 'true'
        }
    
    def export_config(self) -> Dict[str, Any]:
        """Export complete configuration"""
        return {
            'app': self.get_app_config(),
            'database': self.get_database_config(),
            'google_api': self.get_google_api_config(),
            'security': self.get_security_config(),
            'monitoring': self.get_monitoring_config(),
            'feature_flags': self.get_feature_flags()
        }

if __name__ == '__main__':
    config = ProductionConfig()
    print(json.dumps(config.export_config(), indent=2))
