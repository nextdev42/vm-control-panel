import socket
import struct
import random
import subprocess
import time
import argparse
import sys

def random_mac():
    """Generate a locally administered MAC address."""
    return [0x02, 0x00, 0x00,
            random.randint(0x00, 0x7f),
            random.randint(0x00, 0xff),
            random.randint(0x00, 0xff)]

def mac_to_bytes(mac):
    return bytes(mac)

def create_dhcp_discover(mac):
    """Create a minimal DHCPDISCOVER packet."""
    xid = random.randint(0, 0xFFFFFFFF)
    mac_bytes = mac_to_bytes(mac)

    dhcp_packet = struct.pack(
        '!BBBBIHHIIII16s64s128sI',
        1, 1, 6, 0, xid, 0, 0x8000,
        0, 0, 0, 0,
        mac_bytes + b'\x00' * 10,
        b'\x00' * 64,
        b'\x00' * 128,
        0x63825363  # Magic cookie
    )

    # DHCP options
    options = b'\x35\x01\x01'  # DHCP Discover
    options += b'\x37\x03\x01\x03\x06'  # Parameter request list
    options += b'\xff'  # End option

    return dhcp_packet + options, xid

def parse_offer(data):
    """Extract offered IP from DHCP packet."""
    return socket.inet_ntoa(data[16:20])

def send_dhcp(interface):
    """Send DHCPDISCOVER and receive DHCPOFFER."""
    mac = random_mac()
    packet, xid = create_dhcp_discover(mac)

    try:
        sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
        sock.bind((interface, 0))
    except PermissionError:
        print("[!] Must be run with sudo or root privileges.")
        sys.exit(1)
    except Exception as e:
        print(f"[!] Socket error: {e}")
        sys.exit(1)

    ethernet_header = struct.pack('!6s6sH',
                                  b'\xff\xff\xff\xff\xff\xff',
                                  mac_to_bytes(mac),
                                  0x0800)

    # IPv4 + UDP headers (mocked, not used by DHCP relay but needed to construct the frame)
    ip_header = b'\x45\x10\x01\x48\x00\x00\x00\x00\x40\x11\xa6\xec' + \
                b'\x00\x00\x00\x00' + b'\xff\xff\xff\xff'

    udp_header = struct.pack('!HHHH', 68, 67, len(packet) + 8, 0)

    full_packet = ethernet_header + ip_header + udp_header + packet

    print(f"[+] Sending DHCP Discover from interface: {interface}")
    sock.send(full_packet)

    while True:
        raw = sock.recv(4096)
        if raw[42:46] == struct.pack("!I", xid):
            offer_ip = parse_offer(raw[46:])
            print(f"[✓] DHCP Offer received: {offer_ip}")
            return offer_ip

def assign_ip(interface, ip):
    """Assign IP address to interface using iproute2."""
    print(f"[=] Assigning IP {ip} to interface {interface}")
    subprocess.run(["sudo", "ip", "addr", "flush", "dev", interface])
    subprocess.run(["sudo", "ip", "addr", "add", f"{ip}/24", "dev", interface])
    subprocess.run(["sudo", "ip", "link", "set", interface, "up"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DHCP Client Simulator")
    parser.add_argument("-i", "--interface", default="vpc0", help="Network interface to use (default: vpc0)")
    args = parser.parse_args()

    try:
        ip = send_dhcp(args.interface)
        time.sleep(1)
        assign_ip(args.interface, ip)
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user.")
        sys.exit(0)
