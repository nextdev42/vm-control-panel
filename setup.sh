#!/bin/bash

set -e  # Exit on any error for safety

echo "[*] Checking eth1 dummy interface..."

# Create eth1 dummy interface if it doesn't exist
if ! ip link show eth1 &>/dev/null; then
  sudo ip link add eth1 type dummy
  sudo ip link set eth1 up
fi

# Assign static IP address to eth1 (ignore if already assigned)
sudo ip addr add 192.168.56.1/24 dev eth1 2>/dev/null || true

# Enable IP forwarding
echo "[*] Enabling IP forwarding..."
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward

# Set up NAT (MASQUERADE) - add only if missing
sudo iptables -t nat -C POSTROUTING -o eth0 -j MASQUERADE 2>/dev/null || \
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# Configure dnsmasq
echo "[*] Configuring dnsmasq..."
cat <<EOF | sudo tee /etc/dnsmasq.conf
interface=eth1
dhcp-range=192.168.56.10,192.168.56.100,12h
bind-interfaces
EOF

# Restart dnsmasq
echo "[*] Restarting dnsmasq..."
if command -v systemctl &>/dev/null; then
  sudo systemctl restart dnsmasq || true
elif command -v service &>/dev/null; then
  sudo service dnsmasq restart || true
else
  # fallback: kill existing and start fresh
  sudo pkill dnsmasq || true
  sudo dnsmasq --conf-file=/etc/dnsmasq.conf &
fi

# Create admin user if not exists
if ! id -u webadmin >/dev/null 2>&1; then
  echo "[*] Creating webadmin user..."
  sudo useradd -m -s /bin/bash webadmin
  echo 'webadmin:nextdev123' | sudo chpasswd
  sudo usermod -aG sudo webadmin
  echo 'webadmin ALL=(ALL) NOPASSWD:ALL' | sudo tee -a /etc/sudoers
fi

echo "[*] Setup completed!"
