"""Local streaming adapters with bounded reconnect and no secret-bearing output."""

import time
from urllib.parse import quote, urlparse, urlunparse

import cv2
import numpy as np
import requests
from requests.auth import HTTPDigestAuth

from backend.src.local.discovery import discover, local_address


class CameraError(Exception):
    pass


def refresh(camera):
    if camera["kind"] == "fixture":
        return camera
    identity = camera.get("identity")
    if not identity:
        raise CameraError("missing_device_identity")
    candidates = discover(camera["kind"])
    matches = [
        candidate
        for candidate in candidates
        if identity in candidate.get("identities", [candidate.get("identity")])
    ]
    if len(matches) > 1:
        raise CameraError("ambiguous_device_identity")
    if not matches:
        raise CameraError(
            "device_not_found: check power, same LAN, multicast, local streaming"
        )
    return {**camera, **matches[0], "identity": identity}


def stream(camera, credentials=None):
    credentials = credentials or {}
    kind = camera["kind"]
    user, password = credentials.get("username", ""), credentials.get("password", "")
    if kind == "doorbird":
        # Requests handles auth outside the URL, disables redirects and env proxies.
        session = requests.Session()
        session.trust_env = False
        try:
            response = session.get(
                f"http://{camera['host']}:{camera['port']}/bha-api/video.cgi",
                auth=HTTPDigestAuth(user, password),
                stream=True,
                timeout=(5, 10),
                allow_redirects=False,
            )
            if response.status_code != 200:
                raise CameraError(
                    "authentication_or_permission"
                    if response.status_code in (401, 403)
                    else "stream_unavailable"
                )
            with response:
                buffer = b""
                for part in response.iter_content(8192):
                    buffer += part
                    if len(buffer) > 4_000_000:
                        raise CameraError("invalid_stream")
                    while True:
                        start = buffer.find(b"\xff\xd8")
                        end = buffer.find(b"\xff\xd9", max(start, 0))
                        if start < 0 or end < 0:
                            break
                        frame = cv2.imdecode(
                            np.frombuffer(buffer[start : end + 2], dtype=np.uint8),
                            cv2.IMREAD_COLOR,
                        )
                        buffer = buffer[end + 2 :]
                        if frame is not None:
                            yield frame
        except requests.RequestException:
            raise CameraError("stream_disconnected") from None
        finally:
            session.close()
        return
    if kind == "onvif":
        from pathlib import Path

        import onvif
        from onvif import SERVICES, ONVIFService
        from zeep.transports import Transport

        class ScopedSession(requests.Session):
            def request(self, method, url, **kwargs):
                parsed = urlparse(url)
                if parsed.scheme != "http" or parsed.hostname != camera["host"]:
                    raise CameraError("unsafe_service_address")
                kwargs["allow_redirects"] = False
                kwargs["timeout"] = (5, 10)
                response = super().request(method, url, **kwargs)
                if response.is_redirect:
                    raise CameraError("unsafe_service_redirect")
                return response

        session = ScopedSession()
        session.trust_env = False
        transport = Transport(session=session, timeout=10, operation_timeout=10)

        def service(name, address):
            if urlparse(address).hostname != camera["host"]:
                raise CameraError("unsafe_service_address")
            definition = SERVICES[name]
            wsdl = Path(onvif.__file__).parent.parent / "wsdl" / definition["wsdl"]
            return ONVIFService(
                address,
                user,
                password,
                str(wsdl),
                no_cache=True,
                binding_name="{" + definition["ns"] + "}" + definition["binding"],
                transport=transport,
            )

        device = service("devicemgmt", camera["xaddr"])
        capabilities = device.GetCapabilities({"Category": "Media"})
        media = service("media", capabilities.Media.XAddr)
        profiles = media.GetProfiles()
        if not profiles:
            raise CameraError("no_media_profile")
        uri = media.GetStreamUri(
            {
                "StreamSetup": {
                    "Stream": "RTP-Unicast",
                    "Transport": {"Protocol": "RTSP"},
                },
                "ProfileToken": profiles[0].token,
            }
        ).Uri
        parsed = urlparse(uri)
        if (
            parsed.scheme != "rtsp"
            or parsed.hostname != camera["host"]
            or not local_address(parsed.hostname)
        ):
            raise CameraError("unsafe_stream_address")
        host = parsed.hostname + (f":{parsed.port}" if parsed.port else "")
        source = urlunparse(
            parsed._replace(
                netloc=f"{quote(user, safe='')}:{quote(password, safe='')}@{host}"
            )
        )
    elif kind == "usb":
        source = camera["index"]
    elif kind == "fixture":
        source = camera["path"]
    else:
        raise CameraError("unsupported_camera")
    from backend.src.camera import open_camera

    cap = open_camera(source)
    try:
        if not cap.isOpened():
            raise CameraError("stream_open_failed")
        while True:
            ok, frame = cap.read()
            if not ok:
                return
            yield frame
            if kind == "fixture":
                time.sleep(0.1)
    finally:
        cap.release()


def identify_doorbird(candidates, credentials):
    """One Digest information request per independently confirmed DoorBird.

    Never try password variants, non-DoorBird devices, redirects or settings APIs.
    Returns the first authenticated identity and stops. This does not detect
    multiple devices sharing credentials; explicit selection overrides matching.
    """
    from requests.auth import HTTPDigestAuth

    session = requests.Session()
    session.trust_env = False
    try:
        for camera in candidates[:16]:
            if camera["kind"] != "doorbird":
                continue
            try:
                response = session.get(
                    f"http://{camera['host']}:{camera['port']}/bha-api/info.cgi",
                    auth=HTTPDigestAuth(
                        credentials["username"], credentials["password"]
                    ),
                    timeout=(3, 5),
                    allow_redirects=False,
                )
                if response.status_code == 200:
                    value = response.json()
                    if isinstance(value, dict) and isinstance(value.get("BHA"), dict):
                        return camera
            except (requests.RequestException, ValueError):
                pass
            time.sleep(1.1)
    finally:
        session.close()
    return None
