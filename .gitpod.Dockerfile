# .gitpod.Dockerfile

FROM python:3.11-slim

USER root

RUN apt-get update && apt-get install -y \
    iproute2 \
    iputils-ping \
    net-tools \
    dnsmasq \
    sudo \
    netcat \
    curl \
    systemctl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY requirements.txt /workspace/

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /workspace

RUN chmod +x setup.sh

CMD ["bash"]
