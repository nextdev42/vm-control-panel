# .gitpod.Dockerfile
FROM python:3.10-slim

# Install system dependencies, including git
RUN apt-get update && apt-get install -y \
    git \
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

# Upgrade pip
RUN python3 -m ensurepip --upgrade
RUN pip3 install --upgrade pip

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose Flask port
EXPOSE 5000
