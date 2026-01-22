# Use official Playwright Python image (same as main project)
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY anvisa_main.py .
COPY anvisa_crawler.py .

# Install Playwright browsers (Chromium only for speed)
RUN playwright install chromium

# Expose port
EXPOSE 8000

# Start command
CMD ["python", "anvisa_main.py"]
