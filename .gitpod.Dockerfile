FROM python:3.10-slim

# Install system dependencies, including Docker CLI
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
    docker.io \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace/app

RUN python3 -m ensurepip --upgrade
RUN pip3 install --upgrade pip

COPY requirements.txt .
RUN pip3 install -r requirements.txt

RUN echo 'gitpod ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/gitpod

COPY . .

EXPOSE 5000
