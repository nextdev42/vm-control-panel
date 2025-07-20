# app/routes.py

import os
import subprocess
from flask import Blueprint, render_template, request, redirect, url_for, flash

main = Blueprint("main", __name__)

def get_interfaces():
    result = subprocess.run(['ip', '-o', 'addr', 'show'], capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')
    interfaces = {}
    for line in lines:
        parts = line.split()
        iface = parts[1]
        ip = parts[3] if len(parts) > 3 and '/' in parts[3] else None
        if ip:
            interfaces[iface] = ip
    return interfaces

@main.route("/")
def index():
    interfaces = get_interfaces()
    return render_template("index.html", interfaces=interfaces)

@main.route("/add_user", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        subprocess.call(['useradd', '-m', '-s', '/bin/bash', username])
        subprocess.call(['chpasswd'], input=f"{username}:{password}".encode())
        subprocess.call(['usermod', '-aG', 'sudo', username])
        flash(f"User {username} added successfully!", "success")
        return redirect(url_for("main.add_user"))
    return render_template("add_user.html")

@main.route("/set_ip", methods=["GET", "POST"])
def set_ip():
    if request.method == "POST":
        iface = request.form["interface"]
        ipaddr = request.form["ip"]
        subprocess.call(["ip", "addr", "flush", "dev", iface])
        subprocess.call(["ip", "addr", "add", ipaddr, "dev", iface])
        subprocess.call(["ip", "link", "set", iface, "up"])
        flash(f"IP {ipaddr} set on {iface}", "success")
        return redirect(url_for("main.set_ip"))
    interfaces = get_interfaces()
    return render_template("set_ip.html", interfaces=interfaces)

@main.route("/toggle_dhcp", methods=["POST"])
def toggle_dhcp():
    action = request.form.get("action")
    if action == "enable":
        subprocess.call(["systemctl", "start", "dnsmasq"])
    else:
        subprocess.call(["systemctl", "stop", "dnsmasq"])
    flash(f"DHCP {action}d via dnsmasq", "success")
    return redirect(url_for("main.index"))

@main.route("/network_test", methods=["GET", "POST"])
def network_test():
    result = ""
    if request.method == "POST":
        target = request.form["target"]
        result = subprocess.getoutput(f"ping -c 4 {target}")
    return render_template("network_test.html", result=result)
