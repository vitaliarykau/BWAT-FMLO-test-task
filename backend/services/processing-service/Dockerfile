FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY processing-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY processing-service/app/ ./app/
COPY common /common
RUN pip install /common

# Run the processing worker
CMD ["python", "app/main.py"] 