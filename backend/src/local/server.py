"""Loopback-only static gallery/API with cookie authentication and SSE revisions."""

import hmac
import json
import mimetypes
import re
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

from backend.src.local.config import ROOT


def make_server(config, store):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args):
            pass

        def authorized(self):
            cookie = SimpleCookie()
            try:
                cookie.load(self.headers.get("Cookie", ""))
                value = cookie["ghostbusters"].value if "ghostbusters" in cookie else ""
                return hmac.compare_digest(value, config["token"])
            except Exception:
                return False

        def respond(self, code, data, kind="application/json", cookie=None):
            data = data if isinstance(data, bytes) else json.dumps(data).encode()
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Frame-Options", "DENY")
            if cookie:
                self.send_header("Set-Cookie", cookie)
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            if self.path != "/api/session":
                return self.respond(404, {})
            # JSON + no CORS prevents cross-origin form login.
            # The token is never a URL query.
            if self.headers.get("Content-Type") != "application/json":
                return self.respond(415, {})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size < 1024:
                    return self.respond(400, {})
                payload = json.loads(self.rfile.read(size))
                if not isinstance(payload, dict):
                    return self.respond(400, {})
                token = payload.get("token", "")
                if not isinstance(token, str) or not hmac.compare_digest(
                    token, config["token"]
                ):
                    return self.respond(401, {})
                return self.respond(
                    200,
                    {"ok": True},
                    cookie="ghostbusters="
                    + config["token"]
                    + "; HttpOnly; SameSite=Strict; Path=/",
                )
            except (ValueError, TypeError):
                return self.respond(400, {})

        def do_GET(self):
            path = urlparse(self.path).path
            if path.startswith("/api/"):
                if not self.authorized():
                    return self.respond(
                        401,
                        {
                            "error": (
                                "Open the private gallery link from ghostbusters "
                                "local link."
                            )
                        },
                    )
                if path == "/api/status":
                    return self.respond(
                        200,
                        dict(installation=config["installation"], **store.snapshot()),
                    )
                if path == "/api/events":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("Connection", "close")
                    self.end_headers()
                    try:
                        while True:
                            snapshot = store.snapshot()
                            self.wfile.write(
                                (
                                    "event: status\ndata: "
                                    + json.dumps(snapshot)
                                    + "\n\n"
                                ).encode()
                            )
                            self.wfile.flush()
                            time.sleep(2)
                    except (BrokenPipeError, ConnectionResetError):
                        return
                match = re.fullmatch(r"/api/images/([a-f0-9]{32})\.jpg", path)
                if match:
                    image = store.images / (match[1] + ".jpg")
                    if image.is_file():
                        return self.respond(200, image.read_bytes(), "image/jpeg")
                return self.respond(404, {})
            base = (ROOT / "frontend/out").resolve()
            target = (base / unquote(path).lstrip("/")).resolve()
            if not target.is_relative_to(base):
                return self.respond(404, {})
            if target.is_dir():
                target = target / "index.html"
            if not target.is_file():
                return self.respond(
                    404, {"error": "Build the local frontend: ghostbusters local build"}
                )
            return self.respond(
                200,
                target.read_bytes(),
                mimetypes.guess_type(target.name)[0] or "application/octet-stream",
            )

    server = ThreadingHTTPServer(("127.0.0.1", config["port"]), Handler)
    server.daemon_threads = True
    return server
