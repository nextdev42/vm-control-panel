# .gitpod.Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /workspace/app

# Install required system packages
RUN apt update && \
    apt install -y --no-install-recommends \
    net-tools iproute2 dnsmasq iputils-ping sudo && \
    apt clean && rm -rf /var/lib/apt/lists/*

# Optional: add a non-root user (Gitpod uses root by default)
RUN useradd -m developer && echo "developer ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Default command
CMD ["python", "run.py"]
