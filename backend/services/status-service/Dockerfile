FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY status-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY status-service/app/ ./app/
COPY common /common
RUN pip install /common

# Expose the application port
EXPOSE 8002

# Run the application
CMD ["python", "app/main.py"]