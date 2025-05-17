# ---------- Build stage ----------
    FROM python:3.11-slim AS base
    WORKDIR /app
    
    # Ensure project directory is on PYTHONPATH for module resolution
    ENV PYTHONPATH="${PYTHONPATH}:/app"
    
    # Install deps first for cache efficiency
    COPY requirements.txt ./
    RUN pip install --no-cache-dir -r requirements.txt
    
    COPY . .
    
    # Default command runs tests
    CMD ["pytest", "-q"]