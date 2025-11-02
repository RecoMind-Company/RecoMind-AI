# Base Image with Python 3.10
FROM python:3.10-slim-bullseye

# Install SQL Server ODBC Driver dependencies (KEEP THIS)
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    curl \
    gnupg \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Copy requirements and install Python libraries
# (This file now includes celery, redis, gevent, python-dotenv)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code 
# (This copies api.py, pipeline.py, celery_worker.py, and the 'core' folder)
COPY . /app

# Expose the new API port
EXPOSE 8000

# --- [MODIFICATION] ---
# Set the new Uvicorn startup command
# (Replaces the old Gunicorn command)
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]