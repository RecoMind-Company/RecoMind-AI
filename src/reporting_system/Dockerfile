# -----------------------------------------------------------------
# --- Base Image ---
# -----------------------------------------------------------------
FROM python:3.10-slim-buster

# -----------------------------------------------------------------
# --- System Dependencies (for pyodbc) ---
# -----------------------------------------------------------------
# (This part remains the same, it installs MS ODBC Driver)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    unixodbc-dev \
    && \
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg && \
    curl -fsSL https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 && \
    apt-get purge -y curl gnupg && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------
# --- Python Dependencies ---
# -----------------------------------------------------------------
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------
# --- Application Code ---
# -----------------------------------------------------------------
# [MODIFICATION]
# Instead of 'COPY src/ /app/src', we now copy everything 
# from your current folder (reporting_system) into /app
COPY . .

# -----------------------------------------------------------------
# --- Configuration & Execution ---
# -----------------------------------------------------------------
ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# [MODIFICATION]
# The command changes because api.py is now in the root of /app
# We changed "src.reporting_system.api:app" to "api:app"
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

