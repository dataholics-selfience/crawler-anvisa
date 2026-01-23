FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python files
COPY anvisa_main.py .
COPY anvisa_crawler.py .
COPY anvisa_crawler_v2.py .

# Railway uses PORT env variable
ENV PORT=8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD sh -c "curl -f http://localhost:${PORT}/health || exit 1"

# Run FastAPI
CMD sh -c "uvicorn anvisa_main:app --host 0.0.0.0 --port ${PORT:-8080}"
