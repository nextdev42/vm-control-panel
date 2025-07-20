# deploy.sh
#!/bin/bash

# Build and run the Docker container with two network interfaces

docker build -t vm-control-panel .

docker network create \
  --driver=bridge \
  --subnet=192.168.100.0/24 \
  lan_net || true

docker run --privileged --rm -d \
  --name vm_control_panel \
  -p 5000:5000 \
  --network bridge \
  --network-alias public \
  --cap-add=NET_ADMIN \
  --cap-add=SYS_MODULE \
  --device /dev/net/tun \
  --sysctl net.ipv4.ip_forward=1 \
  --network lan_net \
  vm-control-panel

echo "App is running at http://localhost:5000"
