# Dockerfile for RecoMind Copilot Service
# Build context is the 'copilot' directory

# --- Base Image ---
FROM python:3.11-slim-bookworm

# --- Install Microsoft ODBC Driver 17 for SQL Server ---
# Required for 'pyodbc' to connect to MS SQL Server
RUN sed -i 's/deb.debian.org/cdn-fastly.deb.debian.org/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        gnupg \
        unixodbc-dev \
    # Add Microsoft repository with GPG key
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    # Clean up
    && apt-get -y purge curl gnupg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# --- Python Environment ---
WORKDIR /app

# Install uv for extremely fast dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy requirements first for Docker cache optimization
COPY requirements.txt .

# Install Python dependencies using uv (utilizing build cache)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -r requirements.txt

# Copy application code
COPY . .

# --- Runtime ---
# Expose the API port
EXPOSE 8002

# Default command: Run the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
