#!/bin/bash

# Build Docker image
docker build -t vm-control-panel .

# Create custom LAN network (if it doesn't already exist)
docker network inspect lan_net >/dev/null 2>&1 || \
docker network create \
  --driver=bridge \
  --subnet=192.168.100.0/24 \
  --gateway=192.168.100.1 \
  lan_net

# Run container with no network first (we will attach 2 later)
docker run --privileged --rm -d \
  --name vm_control_panel \
  --network none \
  --cap-add=NET_ADMIN \
  --cap-add=SYS_MODULE \
  --device /dev/net/tun \
  --sysctl net.ipv4.ip_forward=1 \
  -p 5000:5000 \
  vm-control-panel

# Attach to default bridge for public access
docker network connect bridge vm_control_panel

# Attach to custom LAN network (eth1 equivalent)
docker network connect lan_net vm_control_panel

echo "App is running at http://localhost:5000"
