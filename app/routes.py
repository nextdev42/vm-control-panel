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
            if iface == "lo":
                continue
            ip = parts[3] if len(parts) > 3 and '/' in parts[3] else None
            interfaces[iface] = ip or "No IP assigned"
        return interfaces
    except subprocess.CalledProcessError:
        return {}

@main.route("/")
def index():
    interfaces = get_interfaces()
    return render_template("index.html", interfaces=interfaces)

@main.route("/set_ip", methods=["GET", "POST"])
def set_ip():
    if request.method == "POST":
        iface = request.form.get("interface", "").strip()
        ipaddr = request.form.get("ip", "").strip()

        if iface != "eth1":
            flash("Samahani, unaweza kuweka IP statiki tu kwa eth1.", "warning")
            return redirect(url_for("main.set_ip"))

        if not ipaddr:
            flash("Tafadhali andika IP address.", "danger")
            return redirect(url_for("main.set_ip"))

        try:
            subprocess.run(["sudo", "ip", "addr", "flush", "dev", iface], check=True)
            subprocess.run(["sudo", "ip", "addr", "add", ipaddr, "dev", iface], check=True)
            subprocess.run(["sudo", "ip", "link", "set", iface, "up"], check=True)
            flash(f"IP {ipaddr} imewekwa kwa {iface}", "success")
        except subprocess.CalledProcessError as e:
            flash(f"Imeshindikana kuweka IP: {e}", "danger")

        return redirect(url_for("main.set_ip"))

    interfaces = get_interfaces()
    return render_template("set_ip.html", interfaces=interfaces)

@main.route("/toggle_dhcp", methods=["GET", "POST"])
def toggle_dhcp():
    if request.method == "POST":
        action = request.form.get("action")
        iface = request.form.get("interface")

        if iface != "eth1":
            flash("DHCP inaweza kuanzishwa au kuzimwa tu kwa eth1.", "warning")
            return redirect(url_for("main.index"))

        if action not in ("enable", "disable"):
            flash("Tafadhali chagua kitendo halali cha DHCP.", "danger")
            return redirect(url_for("main.index"))

        try:
            if action == "enable":
                subprocess.run(["sudo", "systemctl", "start", "dnsmasq"], check=True)
            else:
                subprocess.run(["sudo", "systemctl", "stop", "dnsmasq"], check=True)
            flash(f"DHCP ime{action}wa kwa interface {iface}.", "success")
        except subprocess.CalledProcessError as e:
            flash(f"Imeshindikana kufanya mabadiliko ya DHCP: {e}", "danger")

        return redirect(url_for("main.index"))

    # GET method: show toggle form
    return render_template("toggle_dhcp.html")
