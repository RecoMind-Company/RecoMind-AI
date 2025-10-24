# Base Image with Python 3.10 and Ubuntu 20.04 (LTS)
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
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code 
COPY . /app

# Set the Gunicorn startup command (Final command to run the app)
CMD ["python", "-m", "gunicorn", "-w", "1", "--timeout", "400", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8080", "main:app"]