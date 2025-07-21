import os
import subprocess
from flask import Blueprint, render_template, request, redirect, url_for, flash

main = Blueprint("main", __name__)

@main.route("/")
def index():
    return redirect(url_for("main.set_ip"))

def get_ip_address(interface):
    try:
        result = subprocess.check_output(["ip", "addr", "show", interface], text=True)
        for line in result.splitlines():
            line = line.strip()
            if line.startswith("inet "):
                return line.split()[1]  # Return IP with CIDR
        return "Hakuna IP"
    except subprocess.CalledProcessError:
        return "Interface haipo"

def is_dnsmasq_running():
    try:
        output = subprocess.check_output(["ps", "aux"], text=True)
        return "dnsmasq" in output
    except Exception:
        return False

@main.route("/set_ip", methods=["GET", "POST"])
def set_ip():
    if request.method == "POST":
        iface = request.form.get("interface")
        ip_address = request.form.get("ip_address")
        netmask = request.form.get("netmask")

        try:
            subprocess.run(["ip", "addr", "flush", "dev", iface], check=True)
            subprocess.run(["ip", "addr", "add", f"{ip_address}/{netmask}", "dev", iface], check=True)
            subprocess.run(["ip", "link", "set", iface, "up"], check=True)
            flash(f"✅ IP {ip_address}/{netmask} imewekwa kwenye {iface}", "success")
        except subprocess.CalledProcessError as e:
            flash(f"❌ Hitilafu wakati wa kuweka IP: {str(e)}", "danger")

        return redirect(url_for("main.set_ip"))

    try:
        interfaces_output = subprocess.check_output(["ip", "link", "show"], text=True)
        interfaces = [line.split(":")[1].strip() for line in interfaces_output.splitlines() 
                      if ":" in line and not line.strip().startswith("link")]
    except subprocess.CalledProcessError:
        interfaces = []

    ip_data = {iface: get_ip_address(iface) for iface in interfaces}
    dhcp_status = is_dnsmasq_running()
    return render_template("set_ip.html", interfaces=ip_data, dhcp_status=dhcp_status)

@main.route("/toggle_dhcp", methods=["POST"])
def toggle_dhcp():
    interface = request.form.get("interface")
    action = request.form.get("action")

    if interface != "eth1":
        flash("❌ DHCP inaweza kuanzishwa au kuzimwa tu kwa interface ya eth1.", "danger")
        return redirect(url_for("main.set_ip"))

    DNSMASQ = "/usr/sbin/dnsmasq"
    PKILL = "/usr/bin/pkill"

    if not os.path.exists(DNSMASQ):
        flash("❌ dnsmasq haipatikani kwenye mfumo huu.", "danger")
        return redirect(url_for("main.set_ip"))

    try:
        if action == "enable":
            subprocess.run([PKILL, "dnsmasq"], stderr=subprocess.DEVNULL)
            subprocess.run([
                DNSMASQ,
                "--interface=eth1",
                "--dhcp-range=192.168.1.100,192.168.1.200,12h"
            ], check=True)
            flash("✅ DHCP imewezeshwa kikamilifu kwa eth1 (dnsmasq imeanzishwa).", "success")
        elif action == "disable":
            subprocess.run([PKILL, "dnsmasq"], check=True)
            flash("⚠️ DHCP imezimwa kikamilifu kwa eth1 (dnsmasq imesitishwa).", "warning")
        else:
            flash("❓ Hatua haijafahamika. Tafadhali chagua 'enable' au 'disable'.", "danger")
    except subprocess.CalledProcessError as e:
        flash(f"❌ Hitilafu wakati wa kubadili DHCP: {e}", "danger")

    return redirect(url_for("main.set_ip"))

@main.route("/add_user", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Tafadhali jaza jina la mtumiaji na password.", "danger")
            return redirect(url_for("main.add_user"))

        try:
            subprocess.run(['sudo', 'useradd', '-m', '-s', '/bin/bash', username], check=True)
            subprocess.run(['sudo', 'chpasswd'], input=f"{username}:{password}".encode(), check=True)
            subprocess.run(['sudo', 'usermod', '-aG', 'sudo', username], check=True)
            flash(f"User {username} imeongezwa kwa mafanikio!", "success")
        except subprocess.CalledProcessError as e:
            flash(f"Imeshindikana kuongeza user: {e}", "danger")

        return redirect(url_for("main.add_user"))

    return render_template("add_user.html")
