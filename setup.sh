#!/bin/bash

echo "[*] Checking eth1 dummy interface..."

# Create eth1 dummy interface if it doesn't exist
if ! ip link show eth1 &>/dev/null; then
  ip link add eth1 type dummy
  ip link set eth1 up
fi

# Enable IP forwarding for NAT
echo "[*] Enabling IP forwarding..."
sysctl -w net.ipv4.ip_forward=1

# Set up default dnsmasq config
echo "[*] Configuring dnsmasq..."
cat <<EOF > /etc/dnsmasq.conf
interface=eth1
dhcp-range=192.168.56.10,192.168.56.100,12h
EOF

# Restart dnsmasq
echo "[*] Restarting dnsmasq..."
systemctl restart dnsmasq || service dnsmasq restart || true

# Add webadmin user with sudo privileges
if ! id -u webadmin >/dev/null 2>&1; then
  echo "[*] Creating webadmin user..."
  useradd -m -s /bin/bash webadmin
  echo 'webadmin:nextdev123' | chpasswd
  usermod -aG sudo webadmin
  echo 'webadmin ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
fi

echo "[*] Setup completed!"
