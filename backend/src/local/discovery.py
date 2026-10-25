"""Bounded, unauthenticated Bonjour/WS-Discovery; credentials only after selection."""

import hashlib
import ipaddress
import socket
import time
import uuid
import xml.etree.ElementTree as ET
from urllib.parse import urlparse


def local_address(host):
    try:
        address = ipaddress.ip_address(host)
        return (
            address.is_private
            and not address.is_loopback
            and not address.is_unspecified
        )
    except ValueError:
        return False


def discover_doorbird(seconds=4):
    from zeroconf import ServiceBrowser, Zeroconf

    found = {}

    class Listener:
        def add_service(self, zc, kind, name):
            # Vendor advertises its name on _http._tcp; never probe other HTTP devices.
            if "doorbird" not in name.lower() and "birdguard" not in name.lower():
                return
            info = zc.get_service_info(kind, name, timeout=1200)
            if info:
                addresses = [
                    a
                    for a in info.parsed_addresses()
                    if local_address(a) and ":" not in a
                ]
                if addresses:
                    found[name] = {
                        "id": hashlib.sha256(name.encode()).hexdigest()[:16],
                        "kind": "doorbird",
                        "name": name,
                        "host": addresses[0],
                        "port": info.port,
                        "identity": name,
                    }

        def update_service(self, *args):
            self.add_service(*args)

        def remove_service(self, *args):
            pass

    zc = Zeroconf()
    try:
        browser = ServiceBrowser(zc, "_http._tcp.local.", Listener())
        time.sleep(seconds)
        browser.cancel()
    finally:
        zc.close()
    # A service name alone is not vendor confirmation before authentication.
    import requests

    confirmed = []
    session = requests.Session()
    session.trust_env = False
    try:
        for candidate in list(found.values())[:16]:
            try:
                response = session.get(
                    f"http://{candidate['host']}:{candidate['port']}/",
                    timeout=2,
                    allow_redirects=False,
                )
                if (
                    response.status_code == 200
                    and "doorbird" in response.text[:16384].lower()
                ):
                    confirmed.append(candidate)
            except requests.RequestException:
                continue
    finally:
        session.close()
    return confirmed


def discover_onvif(seconds=3):
    message = (
        "<e:Envelope"
        ' xmlns:e="http://www.w3.org/2003/05/soap-envelope"'
        ' xmlns:a="http://schemas.xmlsoap.org/ws/2004/08/addressing"'
        ' xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery"'
        ' xmlns:n="http://www.onvif.org/ver10/network/wsdl">'
        "<e:Header>"
        f"<a:MessageID>uuid:{uuid.uuid4()}</a:MessageID>"
        "<a:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</a:To>"
        "<a:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</a:Action>"
        "</e:Header>"
        "<e:Body>"
        "<d:Probe>"
        "<d:Types>n:NetworkVideoTransmitter</d:Types>"
        "</d:Probe>"
        "</e:Body>"
        "</e:Envelope>"
    )
    found = {}
    ambiguous = set()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(0.3)
        sock.sendto(message.encode(), ("239.255.255.250", 3702))
        until = time.monotonic() + seconds
        while time.monotonic() < until:
            try:
                data, peer = sock.recvfrom(65535)
                root = ET.fromstring(data)
                endpoint = next(
                    (
                        child.text.strip()
                        for element in root.iter()
                        if element.tag.endswith("}EndpointReference")
                        for child in element
                        if child.tag.endswith("}Address") and child.text
                    ),
                    "",
                )
                if not endpoint:
                    continue
                xaddrs = (
                    next((e.text for e in root.iter() if e.tag.endswith("}XAddrs")), "")
                    or ""
                )
                for address in xaddrs.split():
                    url = urlparse(address)
                    if (
                        url.scheme == "http"
                        and url.hostname == peer[0]
                        and local_address(url.hostname)
                    ):
                        ident = hashlib.sha256(endpoint.encode()).hexdigest()[:16]
                        if ident in ambiguous:
                            continue
                        previous = found.get(ident)
                        if previous and previous["host"] != url.hostname:
                            ambiguous.add(ident)
                            del found[ident]
                            continue
                        found[ident] = {
                            "id": ident,
                            "kind": "onvif",
                            "name": "ONVIF camera " + ident,
                            "host": url.hostname,
                            "port": url.port or 80,
                            "identity": endpoint,
                            "xaddr": address,
                        }
            except (TimeoutError, ET.ParseError, ValueError):
                continue
    return list(found.values())


def discover_usb():
    """Enumerate devices without opening streams; camera permission may be needed."""
    import platform

    if platform.system() == "Darwin":
        import AVFoundation

        devices = AVFoundation.AVCaptureDevice.devicesWithMediaType_(
            AVFoundation.AVMediaTypeVideo
        )
        return [
            {
                "id": "usb-"
                + hashlib.sha256(str(d.uniqueID()).encode()).hexdigest()[:16],
                "kind": "usb",
                "name": str(d.localizedName()),
                "identity": str(d.uniqueID()),
                "index": i,
            }
            for i, d in enumerate(devices)
        ]
    from pathlib import Path

    return [
        {
            "id": "usb-" + p.name,
            "kind": "usb",
            "name": p.name,
            "identity": str(p),
            "index": str(p),
        }
        for p in sorted(Path("/dev").glob("video*"))
    ]


def discover(brand):
    brand = brand.lower()
    if brand == "doorbird":
        # A Bonjour-advertising neighbor must not hide an ARP-only camera.
        # Retain both confirmed identities so a previously selected camera can
        # reconnect even when its discovery mechanism changes.
        merged = {}
        for candidate in discover_doorbird() + doorbird_neighbors():
            key = (candidate["host"], candidate["port"])
            if key not in merged:
                merged[key] = {**candidate, "identities": [candidate["identity"]]}
            elif candidate["identity"] not in merged[key]["identities"]:
                merged[key]["identities"].append(candidate["identity"])
        return list(merged.values())
    if brand == "usb":
        return discover_usb()
    if brand in ("onvif", "rtsp"):
        return discover_onvif()
    raise ValueError(
        "unsupported_camera: use DoorBird, USB, or ONVIF/RTSP with local "
        "streaming enabled; vendor-cloud models need an adapter"
    )


def doorbird_neighbors():
    """Fallback: existing ARP neighbors in IEEE Bird allocations, then public identity.

    No subnet sweep, no credentials, max 16 candidates. ARP MAC is the persisted
    identity so DHCP address changes never cause credentials to follow an old IP.
    """
    import re
    import subprocess

    import requests

    try:
        output = subprocess.run(
            ["arp", "-an"], capture_output=True, text=True, timeout=3, check=True
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    found = []
    session = requests.Session()
    session.trust_env = False
    try:
        attempted = 0
        for host, mac in re.findall(r"\(([^)]+)\) at ([0-9a-fA-F:]+)", output):
            mac = "".join(part.zfill(2) for part in mac.lower().split(":"))
            if not local_address(host) or not mac.startswith(("1ccae37", "58d8a7")):
                continue
            if attempted >= 16:
                break
            attempted += 1
            try:
                response = session.get(
                    "http://" + host + "/", timeout=2, allow_redirects=False
                )
                if (
                    response.status_code == 200
                    and "doorbird" in response.text[:16384].lower()
                ):
                    ident = hashlib.sha256(mac.encode()).hexdigest()[:16]
                    found.append(
                        {
                            "id": ident,
                            "kind": "doorbird",
                            "name": "DoorBird " + ident[-6:],
                            "host": host,
                            "port": 80,
                            "identity": "mac:" + mac,
                        }
                    )
            except requests.RequestException:
                continue
    finally:
        session.close()
    return found
