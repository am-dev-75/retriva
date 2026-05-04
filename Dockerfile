# Use Python 3.12 slim as base image
FROM python:3.12-slim

# Prevent Python from writing pyc files and keep stdout/stderr unbuffered
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Set PYTHONPATH so the app can resolve the retriva package
ENV PYTHONPATH=/app/src

# Set working directory
WORKDIR /app

# Install system dependencies
# - tesseract-ocr & language packs: required by OCRmyPDF for scanning
# - ghostscript: required by OCRmyPDF
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-ita \
    ghostscript \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements to cache them in docker layer
COPY requirements.txt /app/

# Install Python dependencies
# Using --no-cache-dir to reduce image size
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY src /app/src

# Expose ports (8000 for Ingestion API, 8001 for OpenAI API)
EXPOSE 8000 8001

# The default command will just print a help message or run ingestion_api if overridden in compose
CMD ["python", "-m", "retriva.ingestion_api"]
