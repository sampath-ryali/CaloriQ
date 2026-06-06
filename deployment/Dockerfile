# Dockerfile for deploying backend on Render
FROM python:3.11-slim

# Install system dependencies (including OpenCV requirements and Tesseract OCR)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements and install python packages
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ .

# Expose port 5000 for Flask App
EXPOSE 5000

CMD ["python", "app.py"]
