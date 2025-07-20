FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    iproute2 \
    net-tools \
    dnsmasq \
    sudo \
    iputils-ping \
    curl \
    nano \
    && apt-get clean

# Set working directory
WORKDIR /workspace/app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application files (Gitpod mounts the repo later, this is for build cache)
COPY . .
