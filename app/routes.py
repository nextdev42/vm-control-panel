import os
import subprocess
import shutil
from flask import Blueprint, render_template, request, redirect, url_for, flash

main = Blueprint("main", __name__)

# Check if systemctl exists
def systemctl_exists():
    return shutil.which("systemctl") is not None

# Get all interfaces except 'lo'
def get_interfaces():
    try:
        result = subprocess.run(["ip", "-o", "link", "show"], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        interfaces = {}
        for line in lines:
            parts = line.split(": ")
            if len(parts) >= 2:
                index, name = parts[0].split(":")[0], parts[1].split("@")[0]
                if name != "lo":
                    interfaces[name] = {}
        return interfaces
    except subprocess.CalledProcessError as e:
        print(f"Error fetching interfaces: {e}")
        return {}

@main.route("/")
def index():
    interfaces = get_interfaces()
    return render_template("index.html", interfaces=interfaces)

@main.route("/set_ip", methods=["POST"])
def set_ip():
    interface = request.form["interface"]
    ip_address = request.form["ip_address"]
    netmask = request.form["netmask"]

    try:
        subprocess.run(["sudo", "ip", "addr", "flush", "dev", interface], check=True)
        subprocess.run(["sudo", "ip", "addr", "add", f"{ip_address}/{netmask}", "dev", interface], check=True)
        subprocess.run(["sudo", "ip", "link", "set", interface, "up"], check=True)
        flash(f"IP address {ip_address}/{netmask} set on {interface}", "success")
    except subprocess.CalledProcessError as e:
        flash(f"Failed to set IP: {e}", "danger")

    return redirect(url_for("main.index"))

@main.route("/toggle_dhcp", methods=["POST"])
def toggle_dhcp():
    interface = request.form["interface"]
    action = request.form["action"]

    if action == "start":
        try:
            # Kill any existing dnsmasq instances
            subprocess.run(["sudo", "pkill", "dnsmasq"], check=False)
            cmd = [
                "sudo", "dnsmasq",
                f"--interface={interface}",
                "--bind-interfaces",
                "--dhcp-range=192.168.56.100,192.168.56.200,12h"
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            flash(f"DHCP server started on {interface}", "success")
            flash(f"dnsmasq output:\n{proc.stderr}", "info")
        except subprocess.CalledProcessError as e:
            flash(f"Failed to start DHCP: {e}", "danger")
    elif action == "stop":
        subprocess.run(["sudo", "pkill", "dnsmasq"], check=False)
        flash(f"DHCP server stopped on {interface}", "success")

    return redirect(url_for("main.index"))

@main.route("/toggle_nat", methods=["POST"])
def toggle_nat():
    action = request.form["action"]
    if action == "enable":
        try:
            subprocess.run(["sudo", "sysctl", "-w", "net.ipv4.ip_forward=1"], check=True)
            check_nat = subprocess.run(
                ["sudo", "iptables", "-t", "nat", "-C", "POSTROUTING", "-o", "eth0", "-j", "MASQUERADE"],
                capture_output=True
            )
            if check_nat.returncode != 0:
                subprocess.run(["sudo", "iptables", "-t", "nat", "-A", "POSTROUTING", "-o", "eth0", "-j", "MASQUERADE"], check=True)
            flash("NAT enabled", "success")
        except subprocess.CalledProcessError as e:
            flash(f"Failed to enable NAT: {e}", "danger")
    elif action == "disable":
        subprocess.run(["sudo", "sysctl", "-w", "net.ipv4.ip_forward=0"], check=False)
        subprocess.run(["sudo", "iptables", "-t", "nat", "-D", "POSTROUTING", "-o", "eth0", "-j", "MASQUERADE"], check=False)
        flash("NAT disabled", "success")

    return redirect(url_for("main.index"))

@main.route("/add_user", methods=["POST"])
def add_user():
    username = request.form["username"]
    password = request.form["password"]

    try:
        subprocess.run(["sudo", "useradd", "-m", "-s", "/bin/bash", username], check=True)
        subprocess.run(["sudo", "chpasswd"], input=f"{username}:{password}", text=True, check=True)
        subprocess.run(["sudo", "usermod", "-aG", "sudo", username], check=True)
        subprocess.run(["sudo", "bash", "-c", f"echo '{username} ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers"], check=True)
        flash(f"User {username} created and added to sudoers", "success")
    except subprocess.CalledProcessError as e:
        flash(f"Failed to create user: {e}", "danger")

    return redirect(url_for("main.index"))
