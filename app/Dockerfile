# ARM64 base image
FROM --platform=linux/amd64 python:3.9-slim

# Working directory in the container
WORKDIR /app

# System setup
RUN apt-get update && apt-get install -y \
    supervisor \
    cron \
    curl \
    postgresql-client \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Directories with permissions
RUN mkdir -p /etc/supervisor/conf.d /var/log/supervisor /var/run/supervisor /var/log/app /usr/local/bin \
    && mkdir -p /data/sqlite && \
    mkdir -p /home/appuser/.streamlit && \
    chmod 755 /var/log/app /usr/local/bin \
    && chmod -R 777 /data/sqlite

# Non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /data/sqlite

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy configuration files
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY entrypoint.sh /app/
COPY . .

# Streamlit config
RUN echo '[server]\n\
headless = true\n\
enableCORS = false\n\
enableXsrfProtection = true\n\
address = "0.0.0.0"\n\
port = 8501\n\
[browser]\n\
gatherUsageStats = false\n\
[theme]\n\
base = "light"' > /home/appuser/.streamlit/config.toml

# Set permissions
RUN chmod +x /app/entrypoint.sh && \
    chown -R appuser:appuser /home/appuser/.streamlit

# Switch to non-root user
USER appuser

EXPOSE 8501
ENTRYPOINT ["/app/entrypoint.sh"]