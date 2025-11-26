# This Dockerfile assumes the build context is the 'reporting_system' directory
# (which is correct for your structure)

# --- Base Image ---
# Use an official Python image
FROM python:3.11-slim-bookworm

# --- Install Microsoft ODBC Driver 17 for SQL Server ---
# This is necessary for 'pyodbc' and 'aioodbc' to connect to MS SQL Server
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        gnupg \
        unixodbc-dev \
    # We no longer need 'dos2unix' here
    # This is the new, more secure method to add the Microsoft repository
    # 1. Download the GPG key and store it in the trusted keyrings directory
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    # 2. Create the repository list file, pointing to the key we just saved
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
    # 3. Now, run apt-get update (it will trust the key)
    && apt-get update \
    # 4. Install the driver
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    # 5. Clean up
    && apt-get -y purge curl gnupg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# --- Python Environment ---
# Set the working directory *inside* the container
WORKDIR /app

# Copy the requirements file *first* to leverage Docker cache
COPY requirements.txt .

# --- [MODIFICATION] ---
# We removed the 'dos2unix' and 'sed' commands
# because we fixed the file locally in VS Code (by changing CRLF to LF)
# --- [MODIFICATION END] ---

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
# (This copies api.py, pipeline.py, auto_analyst/, data_collection/, etc.)
COPY . .

# --- Runtime ---
# Expose the port the API will run on
EXPOSE 8000

# This is the command that will run when the API container starts
# The 'worker' container will override this using its 'command:' in docker-compose
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

