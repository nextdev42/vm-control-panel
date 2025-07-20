#!/bin/bash

echo "[*] Checking eth1 dummy interface..."

# Create eth1 dummy interface if it doesn't exist
if ! ip link show eth1 &>/dev/null; then
  ip link add eth1 type dummy
  ip link set eth1 up
fi

# Assign static IP address to eth1
ip addr add 192.168.56.1/24 dev eth1 || true

# Enable IP forwarding
echo "[*] Enabling IP forwarding..."
echo 1 > /proc/sys/net/ipv4/ip_forward

# Set up NAT (MASQUERADE)
iptables -t nat -C POSTROUTING -o eth0 -j MASQUERADE 2>/dev/null || \
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# Configure dnsmasq
echo "[*] Configuring dnsmasq..."
cat <<EOF > /etc/dnsmasq.conf
interface=eth1
dhcp-range=192.168.56.10,192.168.56.100,12h
EOF

# Restart dnsmasq
echo "[*] Restarting dnsmasq..."
systemctl restart dnsmasq || service dnsmasq restart || true

# Create admin user if not exists
if ! id -u webadmin >/dev/null 2>&1; then
  echo "[*] Creating webadmin user..."
  useradd -m -s /bin/bash webadmin
  echo 'webadmin:nextdev123' | chpasswd
  usermod -aG sudo webadmin
  echo 'webadmin ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
fi

echo "[*] Setup completed!"
