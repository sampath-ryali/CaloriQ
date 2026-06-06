# Dockerfile for deploying backend + Ollama Qwen service on AWS EC2
FROM python:3.11-slim

# Install system dependencies (including curl for Ollama download and OpenCV requirements)
RUN apt-get update && apt-get install -y \
    curl \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Set work directory
WORKDIR /app

# Copy requirements and install python packages
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ .

# Expose ports: 5000 for Flask App, 11434 for Ollama (optional)
EXPOSE 5000
EXPOSE 11434

# Add startup script to launch Ollama, download Qwen and start Flask backend
RUN echo '#!/bin/bash\n\
ollama serve &\n\
sleep 5\n\
ollama pull qwen2.5:3b\n\
python app.py\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
