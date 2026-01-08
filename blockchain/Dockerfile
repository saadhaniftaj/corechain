FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose blockchain API port
EXPOSE 7050

# Run the blockchain service
CMD ["python", "src/main.py"]
