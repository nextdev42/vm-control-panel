#!/bin/bash

# setup.sh

#!/bin/bash
# Create eth1 dummy interface if it doesn't exist
if ! ip link show eth1 &>/dev/null; then
  sudo ip link add eth1 type dummy
  sudo ip link set eth1 up
fi

# Enable IP forwarding for NAT
sudo sysctl -w net.ipv4.ip_forward=1

# Start dnsmasq if needed
sudo systemctl restart dnsmasq || true


echo "[*] Running initial setup..."

# Enable IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward

# Set up default dnsmasq config
cat <<EOF > /etc/dnsmasq.conf
interface=eth1
dhcp-range=192.168.56.10,192.168.56.100,12h
EOF

# Restart dnsmasq
systemctl restart dnsmasq || service dnsmasq restart

# Add webadmin user with sudo privileges (example)
if ! id -u webadmin >/dev/null 2>&1; then
  useradd -m -s /bin/bash webadmin
  echo 'webadmin:nextdev123' | chpasswd
  usermod -aG sudo webadmin
  echo 'webadmin ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
fi

echo "[*] Setup completed!"
