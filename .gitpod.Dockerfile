# .gitpod.Dockerfile
FROM python:3.10-slim

# Install necessary system packages
RUN apt-get update && apt-get install -y \
    iproute2 \
    net-tools \
    dnsmasq \
    sudo \
    iputils-ping \
    curl \
    nano \
    python3-pip \
    && apt-get clean

# Set working directory
WORKDIR /workspace/app

# Ensure pip is upgraded first
RUN python3 -m ensurepip --upgrade
RUN pip3 install --upgrade pip

# Copy requirements and install
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy the full project
COPY . .

# Expose default port
EXPOSE 5000
