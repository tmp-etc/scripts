#!/usr/bin/env python3
"""
gps_bridge.py — runs on the Raspberry Pi next to Kismet.

Polls your website's /latest endpoint and re-serves the newest fix as NMEA 0183
over a local TCP socket, which Kismet reads with:

    gps=tcp:host=localhost,port=4353

Usage:
    pip install requests
    URL=https://your.site TOKEN=your-secret PORT=4353 python3 gps_bridge.py

Notes:
- Only serves a fix while it's fresh (see MAX_AGE). Stale/absent fixes send the
  NMEA "void" status so Kismet knows it has no lock, rather than pinning you to
  an old point.
- The Pi needs network reach to the website. If you wardrive off-grid, either
  give the Pi a route to the site (phone hotspot / tether) or skip the website
  entirely and feed Kismet from the phone directly (BlueNMEA over TCP).
"""

import os
import time
import socket
import threading
from datetime import datetime, timezone

import requests

URL = os.environ.get("URL", "ürl").rstrip("/")
TOKEN = os.environ.get("TOKEN", "töken")
PORT = int(os.environ.get("PORT", 4353))
POLL_INTERVAL = float(os.environ.get("POLL", 1.0))   # seconds
MAX_AGE = float(os.environ.get("MAX_AGE", 8.0))      # fix older than this = void

_lock = threading.Lock()
_fix = {}  # newest fix from the website


def poll_loop():
    """Continuously fetch /latest into _fix."""
    s = requests.Session()
    while True:
        try:
            r = s.get(f"{URL}/latest", headers={"X-Token": TOKEN}, timeout=4)
            if r.ok:
                data = r.json()
                if "lat" in data and "lon" in data:
                    data["_recv"] = time.time()
                    with _lock:
                        _fix.clear()
                        _fix.update(data)
        except Exception as e:
            print(f"[poll] {e}")
        time.sleep(POLL_INTERVAL)


def _checksum(body: str) -> str:
    c = 0
    for ch in body:
        c ^= ord(ch)
    return f"{c:02X}"


def _sentence(body: str) -> str:
    return f"${body}*{_checksum(body)}\r\n"


def _lat_field(lat: float):
    hemi = "N" if lat >= 0 else "S"
    lat = abs(lat)
    deg = int(lat)
    minutes = (lat - deg) * 60.0
    return f"{deg:02d}{minutes:07.4f}", hemi


def _lon_field(lon: float):
    hemi = "E" if lon >= 0 else "W"
    lon = abs(lon)
    deg = int(lon)
    minutes = (lon - deg) * 60.0
    return f"{deg:03d}{minutes:07.4f}", hemi


def build_nmea():
    """Return GPRMC + GPGGA for the current fix, or a 'void' RMC if stale."""
    with _lock:
        fix = dict(_fix)

    now = datetime.now(timezone.utc)
    hhmmss = now.strftime("%H%M%S.00")
    ddmmyy = now.strftime("%d%m%y")

    fresh = fix and (time.time() - fix.get("_recv", 0)) <= MAX_AGE
    if not fresh:
        # A=valid, V=void. Send void so Kismet knows there's no current lock.
        rmc = _sentence(f"GPRMC,{hhmmss},V,,,,,,,{ddmmyy},,")
        return rmc

    lat_s, lat_h = _lat_field(float(fix["lat"]))
    lon_s, lon_h = _lon_field(float(fix["lon"]))

    speed = fix.get("speed")
    knots = f"{float(speed) * 1.943844:.1f}" if speed not in (None, "") else ""
    course = fix.get("heading")
    course_s = f"{float(course):.1f}" if course not in (None, "") else ""
    alt = fix.get("alt")
    alt_s = f"{float(alt):.1f}" if alt not in (None, "") else ""

    rmc = _sentence(
        f"GPRMC,{hhmmss},A,{lat_s},{lat_h},{lon_s},{lon_h},"
        f"{knots},{course_s},{ddmmyy},,"
    )
    gga = _sentence(
        f"GPGGA,{hhmmss},{lat_s},{lat_h},{lon_s},{lon_h},1,08,0.9,"
        f"{alt_s},M,,M,,"
    )
    return rmc + gga


def serve_client(conn, addr):
    print(f"[tcp] Kismet connected from {addr}")
    try:
        while True:
            conn.sendall(build_nmea().encode("ascii"))
            time.sleep(1.0)
    except (BrokenPipeError, ConnectionResetError, OSError):
        pass
    finally:
        conn.close()
        print(f"[tcp] {addr} disconnected")


def main():
    threading.Thread(target=poll_loop, daemon=True).start()

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", PORT))
    srv.listen(5)
    print(f"[tcp] NMEA server on :{PORT}  ->  Kismet gps=tcp:host=localhost,port={PORT}")
    print(f"[poll] polling {URL}/latest every {POLL_INTERVAL}s")

    while True:
        conn, addr = srv.accept()
        threading.Thread(target=serve_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
