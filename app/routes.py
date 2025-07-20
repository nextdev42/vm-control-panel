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

@main.route("/network_test", methods=["GET", "POST"])
def network_test():
    result = ""
    if request.method == "POST":
        target = request.form.get("target", "").strip()
        if target:
            result = subprocess.getoutput(f"ping -c 4 {target}")
        else:
            result = "Tafadhali andika IP au hostname."
    return render_template("network_test.html", result=result)

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

    # GET method: onyesha form ya toggle DHCP
    return render_template("toggle_dhcp.html")

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

@main.route("/toggle_nat", methods=["GET", "POST"])
def toggle_nat():
    if request.method == "POST":
        action = request.form.get("action")
        iface = request.form.get("interface")

        if iface != "eth1":
            flash("NAT inaweza kuanzishwa au kuzimwa tu kwa eth1.", "warning")
            return redirect(url_for("main.index"))

        if action not in ("enable", "disable"):
            flash("Tafadhali chagua kitendo halali cha NAT.", "danger")
            return redirect(url_for("main.index"))

        try:
            if action == "enable":
                # Enable IP forwarding
                subprocess.run(["sudo", "sysctl", "-w", "net.ipv4.ip_forward=1"], check=True)
                # Setup NAT with iptables masquerade on eth0 (assume eth0 is public interface)
                subprocess.run([
                    "sudo", "iptables", "-t", "nat", "-A", "POSTROUTING",
                    "-o", "eth0", "-j", "MASQUERADE"
                ], check=True)
                flash(f"NAT imewezeshwa kwa interface {iface}.", "success")
            else:
                # Disable NAT (remove masquerade rule)
                subprocess.run([
                    "sudo", "iptables", "-t", "nat", "-D", "POSTROUTING",
                    "-o", "eth0", "-j", "MASQUERADE"
                ], check=True)
                # Disable IP forwarding
                subprocess.run(["sudo", "sysctl", "-w", "net.ipv4.ip_forward=0"], check=True)
                flash(f"NAT imezimwa kwa interface {iface}.", "success")
        except subprocess.CalledProcessError as e:
            flash(f"Imeshindikana kufanya mabadiliko ya NAT: {e}", "danger")

        return redirect(url_for("main.index"))

    interfaces = get_interfaces()
    return render_template("toggle_nat.html", interfaces=interfaces)
