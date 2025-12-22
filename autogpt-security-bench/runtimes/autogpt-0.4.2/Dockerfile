# AutoGPT 0.4.2 Security Testing Runtime
# Minimal Dockerfile - does NOT include source code
# Source must be provided externally via volume mount

FROM python:3.10-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    chromium-driver \
    firefox-esr \
    ca-certificates \
    curl \
    jq \
    wget \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PIP_NO_CACHE_DIR=yes \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="$PATH:/root/.local/bin"

# Copy and install requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Create workspace directory
RUN mkdir -p /app/autogpt/workspace/auto_gpt_workspace

WORKDIR /app

# Entry point for running AutoGPT
# Actual source code will be mounted at /app/autogpt-source
ENTRYPOINT ["python", "-m", "autogpt"]
