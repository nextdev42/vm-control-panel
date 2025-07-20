import subprocess
from flask import Blueprint, render_template, request, redirect, url_for, flash

main = Blueprint("main", __name__)

def get_interfaces():
    try:
        result = subprocess.run(['ip', '-o', 'addr', 'show'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        interfaces = {}
        for line in lines:
            parts = line.split()
            iface = parts[1]
            ip = parts[3] if len(parts) > 3 and '/' in parts[3] else None
            if ip:
                interfaces[iface] = ip
        return interfaces
    except subprocess.CalledProcessError:
        return {}

@main.route("/")
def index():
    interfaces = get_interfaces()
    return render_template("index.html", interfaces=interfaces)

@main.route("/add_user", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if not username or not password:
            flash("Username and password are required.", "danger")
            return redirect(url_for("main.add_user"))
        try:
            subprocess.run(['sudo', 'useradd', '-m', '-s', '/bin/bash', username], check=True)
            subprocess.run(['sudo', 'chpasswd'], input=f"{username}:{password}".encode(), check=True)
            subprocess.run(['sudo', 'usermod', '-aG', 'sudo', username], check=True)
            flash(f"User {username} added successfully!", "success")
        except subprocess.CalledProcessError as e:
            flash(f"Failed to add user: {e}", "danger")
        return redirect(url_for("main.add_user"))
    return render_template("add_user.html")

@main.route("/set_ip", methods=["GET", "POST"])
def set_ip():
    if request.method == "POST":
        iface = request.form.get("interface", "").strip()
        ipaddr = request.form.get("ip", "").strip()
        if not iface or not ipaddr:
            flash("Interface and IP address are required.", "danger")
            return redirect(url_for("main.set_ip"))
        try:
            subprocess.run(["sudo", "ip", "addr", "flush", "dev", iface], check=True)
            subprocess.run(["sudo", "ip", "addr", "add", ipaddr, "dev", iface], check=True)
            subprocess.run(["sudo", "ip", "link", "set", iface, "up"], check=True)
            flash(f"IP {ipaddr} set on {iface}", "success")
        except subprocess.CalledProcessError as e:
            flash(f"Failed to set IP: {e}", "danger")
        return redirect(url_for("main.set_ip"))
    interfaces = get_interfaces()
    return render_template("set_ip.html", interfaces=interfaces)

@main.route("/toggle_dhcp", methods=["POST"])
def toggle_dhcp():
    action = request.form.get("action")
    if action not in ("enable", "disable"):
        flash("Invalid DHCP action.", "danger")
        return redirect(url_for("main.index"))
    try:
        if action == "enable":
            subprocess.run(["sudo", "systemctl", "start", "dnsmasq"], check=True)
        else:
            subprocess.run(["sudo", "systemctl", "stop", "dnsmasq"], check=True)
        flash(f"DHCP {action}d via dnsmasq", "success")
    except subprocess.CalledProcessError as e:
        flash(f"Failed to {action} DHCP: {e}", "danger")
    return redirect(url_for("main.index"))

@main.route("/network_test", methods=["GET", "POST"])
def network_test():
    result = ""
    if request.method == "POST":
        target = request.form.get("target", "").strip()
        if target:
            try:
                result = subprocess.run(
                    ["ping", "-c", "4", target],
                    capture_output=True, text=True, check=True
                ).stdout
            except subprocess.CalledProcessError as e:
                result = f"Ping failed: {e}"
        else:
            result = "Please enter a valid target."
    return render_template("network_test.html", result=result)
