# app/utils.py

import subprocess

def run_command(cmd):
    """Run a shell command and return output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"

def get_network_interfaces():
    """Return a list of network interfaces."""
    output = run_command(['ip', '-o', 'link', 'show'])
    interfaces = []
    for line in output.splitlines():
        parts = line.split(':')
        if len(parts) > 1:
            iface = parts[1].strip()
            if not iface.startswith('lo'):
                interfaces.append(iface)
    return interfaces
