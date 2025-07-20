# Dockerfile

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    iproute2 \
    iputils-ping \
    net-tools \
    dnsmasq \
    sudo \
    netcat \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy and make setup script executable
RUN chmod +x /app/setup.sh

# Run setup script at container start
CMD ["/bin/bash", "-c", "/app/setup.sh && python run.py"]
