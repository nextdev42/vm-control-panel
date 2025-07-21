import socket
import struct
import random
import subprocess
import time

# Replace this with your test interface (like 'vpc0')
INTERFACE = 'eth1'

# Generate a random MAC address
def random_mac():
    return [0x02, 0x00, 0x00, random.randint(0x00, 0x7f), random.randint(0x00, 0xff), random.randint(0x00, 0xff)]

def mac_to_bytes(mac):
    return bytes(mac)

def create_dhcp_discover(mac):
    xid = random.randint(0, 0xFFFFFFFF)
    mac_bytes = mac_to_bytes(mac)
    packet = struct.pack('!BBBBIHHIIII16s64s128sI',
                         1, 1, 6, 0, xid, 0, 0x8000,
                         0, 0, 0, 0,
                         mac_bytes + b'\x00' * 10,
                         b'\x00' * 64,
                         b'\x00' * 128,
                         0x63825363)  # magic cookie
    options = b'\x35\x01\x01'  # DHCP Discover
    options += b'\x37\x03\x01\x03\x06'  # parameter request list
    options += b'\xff'
    return packet + options, xid

def parse_offer(data):
    yiaddr = socket.inet_ntoa(data[16:20])
    return yiaddr

def send_dhcp(interface):
    mac = random_mac()
    packet, xid = create_dhcp_discover(mac)

    sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
    sock.bind((interface, 0))

    ethernet_header = struct.pack('!6s6sH',
                                  b'\xff\xff\xff\xff\xff\xff',
                                  mac_to_bytes(mac),
                                  0x0800)

    ip_header = b'\x45\x10\x01\x48\x00\x00\x00\x00\x40\x11\xa6\xec' + \
                b'\x00\x00\x00\x00' + b'\xff\xff\xff\xff'

    udp_header = struct.pack('!HHHH', 68, 67, len(packet) + 8, 0)

    full_packet = ethernet_header + ip_header + udp_header + packet

    print(f"[+] Sending DHCP Discover on {interface}")
    sock.send(full_packet)

    while True:
        raw = sock.recv(4096)
        if raw[42:46] == struct.pack("!I", xid):
            offer_ip = parse_offer(raw[46:])
            print(f"[✓] Got DHCP Offer: {offer_ip}")
            return offer_ip

# Assign IP to interface (Linux only)
def assign_ip(interface, ip):
    print(f"[=] Assigning IP {ip} to {interface}")
    subprocess.run(["sudo", "ip", "addr", "flush", "dev", interface])
    subprocess.run(["sudo", "ip", "addr", "add", f"{ip}/24", "dev", interface])
    subprocess.run(["sudo", "ip", "link", "set", interface, "up"])

if __name__ == "__main__":
    ip = send_dhcp(INTERFACE)
    time.sleep(1)
    assign_ip(INTERFACE, ip)
