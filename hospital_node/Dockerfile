FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Hospital dashboard port
EXPOSE 3000

# Entrypoint validates env vars and data mount
RUN chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
