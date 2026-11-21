#!/usr/bin/env python3
"""Check the spike server's /health from Moka's VM, via the tailnet tunnel.

Usage: check_from_vm.py <tailnet-ip> [port]

The VM reaches tailnet TCP services only through the runtime tunnel proxy.
This reuses ~/.ssh/tailscale_connect.py (the SSH ProxyCommand helper), which
issues a CONNECT through that proxy using credentials taken from the
HTTPS_PROXY environment variable at run time; nothing is stored here.
"""
import subprocess
import sys

HELPER = "/home/hatch/.ssh/tailscale_connect.py"


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: check_from_vm.py <tailnet-ip> [port]")
        return 2
    host = sys.argv[1]
    port = sys.argv[2] if len(sys.argv) > 2 else "8765"

    request = f"GET /health HTTP/1.0\r\nHost: {host}\r\n\r\n"
    proc = subprocess.run(
        ["python3", HELPER, host, port],
        input=request.encode(),
        capture_output=True,
        timeout=20,
    )
    out = proc.stdout.decode(errors="replace")
    print(out)
    first_line = out.splitlines()[0] if out.splitlines() else ""
    if " 200 " in first_line:
        print("RESULT: reachable (HTTP 200)")
        return 0
    print(f"RESULT: NOT reachable (helper rc={proc.returncode})")
    if proc.stderr:
        print(proc.stderr.decode(errors="replace"))
    return 1


if __name__ == "__main__":
    sys.exit(main())
