FROM python:3.12-slim

WORKDIR /app

# Install system dependencies needed for build and Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium browser and all its system dependencies
# --with-deps installs required system libraries (libnss3, libatk, etc.)
RUN apt-get update && playwright install --with-deps chromium && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY app/ ./app/

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
