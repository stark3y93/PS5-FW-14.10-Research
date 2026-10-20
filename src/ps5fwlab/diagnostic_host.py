"""Restricted static host for two passive diagnostic assets; no portal or proxy."""
import argparse
import hashlib
import ipaddress
import json
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "diagnostics" / "browser"
NETWORKS = tuple(ipaddress.IPv4Network(n) for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"))
CSP = "default-src 'none'; script-src 'self'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; font-src 'none'; media-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"


def validate_bind(address):
    """Do not resolve names or silently bind a wildcard/public interface."""
    try:
        parsed = ipaddress.IPv4Address(address)
    except ipaddress.AddressValueError as exc:
        raise ValueError("--bind must be a literal RFC1918 IPv4 address or 127.0.0.1") from exc
    if str(parsed) != "127.0.0.1" and not any(parsed in network for network in NETWORKS):
        raise ValueError("wildcard, public, link-local and other special bind addresses are not allowed")
    return str(parsed)


def _assets(directory):
    root = Path(directory).resolve(strict=True)
    assets = {}
    for name, mime in (("index.html", "text/html; charset=utf-8"),
                       ("diagnostic.js", "text/javascript; charset=utf-8")):
        path = root / name
        try:
            if path.is_symlink() or path.resolve(strict=True).parent != root or not path.is_file():
                raise ValueError("diagnostic assets must be regular files in the diagnostic directory")
            with path.open("rb") as stream:
                data = stream.read(262145)
        except OSError as exc:
            raise ValueError("required diagnostic asset is missing or unreadable: " + name) from exc
        if not data or len(data) > 262144:
            raise ValueError("diagnostic asset must contain 1 to 262144 bytes: " + name)
        assets["/" + name] = (data, mime)
    return assets


class DiagnosticServer(ThreadingHTTPServer):
    allow_reuse_address = False
    daemon_threads = True

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


class DiagnosticHandler(BaseHTTPRequestHandler):
    server_version = "PassiveDiagnostic/1.0"
    sys_version = ""

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def log_message(self, format, *args):
        # No access/IP/query/body log or result collection.
        pass

    def _reply(self, status, data=b"Unavailable\n", mime="text/plain; charset=utf-8", allow=None):
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Connection", "close")
        if allow:
            self.send_header("Allow", allow)
        self.end_headers()
        self.close_connection = True
        if self.command != "HEAD":
            self.wfile.write(data)

    def do_GET(self):
        hosts = self.headers.get_all("Host", [])
        if len(hosts) != 1 or hosts[0] not in self.server.allowed_hosts:
            self._reply(403)
            return
        # Exact request-target allowlist: no decode, normalize, redirect or listing.
        # BaseHTTPRequestHandler normalizes a leading // before dispatch; use
        # the original parsed request line to preserve our exact allowlist.
        target = self.requestline.split()[1]
        route = "/index.html" if target == "/" else target
        if route not in self.server.assets:
            self._reply(404)
            return
        data, mime = self.server.assets[route]
        self._reply(200, data, mime)

    do_HEAD = do_GET

    def _method_not_allowed(self):
        self._reply(405, allow="GET, HEAD")

    do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = do_CONNECT = do_TRACE = _method_not_allowed


def make_server(address="127.0.0.1", port=8765, directory=None):
    """Bind exactly one address; directory injection is for isolated offline tests."""
    address = validate_bind(address)
    if type(port) is not int or not (port == 0 or 1024 <= port <= 65535):
        raise ValueError("port must be 1024 to 65535 (0 is reserved for internal tests)")
    assets = _assets(ROOT if directory is None else directory)
    server = DiagnosticServer((address, port), DiagnosticHandler)
    server.assets = assets
    authority = address + ":" + str(server.server_port)
    server.allowed_hosts = {authority}
    if server.server_port == 80:
        server.allowed_hosts.add(address)
    if address == "127.0.0.1":
        server.allowed_hosts.add("localhost:" + str(server.server_port))
    return server


def server_manifest(server):
    address, port = server.server_address
    return {"schema": "ps5-diagnostic-host/1", "url": "http://" + address + ":" + str(port) + "/",
            "scope": "PC loopback preview" if address == "127.0.0.1" else "chosen private IPv4 interface",
            "assets": {path: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                       for path, (data, _) in server.assets.items()},
            "console_navigation_established": False,
            "limits": ["HTTP only; no TLS/certificate setup", "No authentication; LAN peers can read these public assets",
                       "No portal, DNS, proxy, forwarding, uploads or result collection",
                       "A URL and successful PC bind do not establish PS5 navigation or reachability"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bind", default="127.0.0.1", help="chosen PC private IPv4; default is PC-only loopback")
    parser.add_argument("--port", type=int, default=8765, help="1024 to 65535, default 8765")
    parser.add_argument("--check", action="store_true", help="validate files/bind, print manifest and close without serving")
    args = parser.parse_args(argv)
    if not 1024 <= args.port <= 65535:
        parser.error("--port must be 1024 to 65535")
    try:
        server = make_server(args.bind, args.port)
    except (OSError, ValueError) as exc:
        parser.error("host not started: " + str(exc))
    try:
        print(json.dumps(server_manifest(server), indent=2), flush=True)
        if not args.check:
            print("Ready. Open the URL shown above. Stop with Ctrl+C. PS5 navigation remains unverified.", flush=True)
            server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
