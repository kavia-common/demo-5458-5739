import platform
import shutil
import subprocess
from datetime import datetime, timezone
from typing import Tuple

from .validators import is_valid_ipv4

# PUBLIC_INTERFACE
def ping_host(ip_address: str, timeout_ms: int = 1000, count: int = 1) -> Tuple[str, str, str]:
    """Ping an IPv4 address and return (status, timestamp_iso, error_message).
    Uses pythonping if available, otherwise falls back to system ping.
    Status is 'online' or 'offline'. Error message may be empty."""
    timestamp = datetime.now(timezone.utc).isoformat()
    if not is_valid_ipv4(ip_address):
        return "offline", timestamp, "Invalid IPv4 address"

    # Try pythonping first
    try:
        from pythonping import ping  # type: ignore
        resp = ping(ip_address, count=count, timeout=timeout_ms / 1000.0, size=40, verbose=False)
        if resp.success():
            return "online", timestamp, ""
        return "offline", timestamp, ""
    except Exception:
        # Fallback to system ping
        pass

    try:
        ping_cmd = "ping"
        if shutil.which(ping_cmd) is None:
            return "offline", timestamp, "No ping utility available"

        system = platform.system().lower()
        if system == "windows":
            # -n count, -w timeout(ms)
            cmd = [ping_cmd, "-n", str(count), "-w", str(timeout_ms), ip_address]
        else:
            # -c count, -W timeout(seconds)
            timeout_s = max(1, int(round(timeout_ms / 1000.0)))
            cmd = [ping_cmd, "-c", str(count), "-W", str(timeout_s), ip_address]
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if r.returncode == 0:
            return "online", timestamp, ""
        return "offline", timestamp, r.stderr.strip() or r.stdout.strip()
    except Exception as e:
        return "offline", timestamp, str(e)
