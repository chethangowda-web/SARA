FROM python:3.11-slim

WORKDIR /workspace

# Install system dependencies required for compilation and pgvector
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt ./

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

ENV PYTHONPATH=/workspace

EXPOSE 8000
