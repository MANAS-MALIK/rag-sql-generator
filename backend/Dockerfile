# ── Stage 1: base image ────────────────────────────────────
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Install system dependencies needed by faiss and python-docx
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (Docker layer caching — faster rebuilds)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend source code
COPY . .

# Expose port 8000 (FastAPI default)
EXPOSE 8000

# Start the server
# --host 0.0.0.0  → accept connections from outside container
# --port 8000     → listen on port 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
