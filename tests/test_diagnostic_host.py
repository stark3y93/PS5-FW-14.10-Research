"""Exercise the real restricted HTTP server, using loopback and tiny fixtures."""
import hashlib
import http.client
import json
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

from ps5fwlab import diagnostic_host as host

ROOT = Path(__file__).resolve().parents[1]


class DiagnosticHostTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name) / "diagnostic"
        self.directory.mkdir()
        (self.directory / "index.html").write_bytes(b"<h1>passive</h1>")
        (self.directory / "diagnostic.js").write_bytes(b"'use strict';")
        (self.directory / "secret.txt").write_text("private", encoding="utf-8")
        (Path(self.temp.name) / "README.md").write_text("outside", encoding="utf-8")

    def serve(self):
        server = host.make_server("127.0.0.1", 0, self.directory)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        def cleanup():
            server.shutdown()
            server.server_close()
            worker.join(timeout=2)
        self.addCleanup(cleanup)
        return server

    def request(self, server, method, path, headers=None, body=None):
        conn = http.client.HTTPConnection(*server.server_address, timeout=3)
        try:
            conn.request(method, path, body=body, headers=headers or {})
            response = conn.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            conn.close()

    def test_only_assets_are_served_with_security_headers_and_correct_head(self):
        server = self.serve()
        for path, content, mime in [("/", b"<h1>passive</h1>", "text/html"),
                                    ("/index.html", b"<h1>passive</h1>", "text/html"),
                                    ("/diagnostic.js", b"'use strict';", "text/javascript")]:
            with self.subTest(path=path):
                code, headers, data = self.request(server, "GET", path)
                self.assertEqual((code, data), (200, content))
                self.assertIn(mime, headers["Content-Type"])
                self.assertEqual(headers["Cache-Control"], "no-store")
                self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
                self.assertIn("connect-src 'none'", headers["Content-Security-Policy"])
                code, headers, data = self.request(server, "HEAD", path)
                self.assertEqual((code, data), (200, b""))
                self.assertEqual(int(headers["Content-Length"]), len(content))

    def test_traversal_other_files_query_strings_and_absolute_targets_fail(self):
        server = self.serve()
        for path in ["/secret.txt", "/../README.md", "/%2e%2e/README.md", "/diagnostic/",
                     "/.git/config", "/diagnostic.js/../secret.txt", "/index.html?result=private",
                     "//index.html", "/%69ndex.html", "http://example.com/index.html"]:
            with self.subTest(path=path):
                code, _, data = self.request(server, "GET", path,
                                             {"Host": "127.0.0.1:" + str(server.server_port)})
                self.assertEqual(code, 404)
                self.assertNotIn(b"private", data)
                self.assertNotIn(b"outside", data)

    def test_upload_methods_do_not_change_assets(self):
        server = self.serve()
        for method in ["POST", "PUT", "PATCH", "DELETE", "OPTIONS", "CONNECT", "TRACE"]:
            code, headers, _ = self.request(server, method, "/index.html", body="replace")
            self.assertEqual(code, 405)
            self.assertEqual(headers["Allow"], "GET, HEAD")
        self.assertEqual((self.directory / "index.html").read_bytes(), b"<h1>passive</h1>")

    def test_unknown_host_and_wrong_port_are_rejected(self):
        server = self.serve()
        for value in ["evil.example", "127.0.0.1:1", "127.0.0.1.evil.example", "localhost.evil"]:
            self.assertEqual(self.request(server, "GET", "/", {"Host": value})[0], 403)

    def test_assets_are_snapshotted_not_read_from_arbitrary_later_paths(self):
        server = self.serve()
        (self.directory / "index.html").write_text("later contents", encoding="utf-8")
        self.assertEqual(self.request(server, "GET", "/")[2], b"<h1>passive</h1>")

    def test_bind_policy_is_explicit_rfc1918_or_loopback_only(self):
        for value in ["192.168.1.50", "10.0.0.2", "172.16.0.2", "172.31.255.254", "127.0.0.1"]:
            self.assertEqual(host.validate_bind(value), value)
        for value in ["0.0.0.0", "8.8.8.8", "localhost", "::", "::1", "169.254.2.1",
                      "192.0.0.1", "100.64.0.1", "172.32.0.2", "127.0.0.2", "10.0.0.999"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                host.validate_bind(value)

    def test_missing_and_oversized_assets_fail_before_binding(self):
        (self.directory / "diagnostic.js").unlink()
        with self.assertRaises(ValueError):
            host.make_server("127.0.0.1", 0, self.directory)
        (self.directory / "diagnostic.js").write_bytes(b"a" * 262145)
        with self.assertRaises(ValueError):
            host.make_server("127.0.0.1", 0, self.directory)

    def test_symlink_asset_is_not_followed(self):
        p = self.directory / "diagnostic.js"
        p.unlink()
        try:
            p.symlink_to(Path(self.temp.name) / "README.md")
        except OSError:
            self.skipTest("symlink creation requires unavailable OS privilege")
        with self.assertRaises(ValueError):
            host.make_server("127.0.0.1", 0, self.directory)

    def test_manifest_binds_hashes_to_exact_served_bytes(self):
        server = self.serve()
        report = host.server_manifest(server)
        self.assertEqual(report["url"], "http://127.0.0.1:" + str(server.server_port) + "/")
        self.assertFalse(report["console_navigation_established"])
        self.assertEqual(report["assets"]["/index.html"]["sha256"], hashlib.sha256(b"<h1>passive</h1>").hexdigest())

    def test_busy_port_is_failure(self):
        server = self.serve()
        with self.assertRaises(OSError):
            host.make_server("127.0.0.1", server.server_port, self.directory)

    def test_duplicate_or_missing_host_is_rejected(self):
        server = self.serve()
        authority = "127.0.0.1:" + str(server.server_port)
        for headers in ["", "Host: " + authority + "\r\nHost: " + authority + "\r\n"]:
            with socket.create_connection(server.server_address, timeout=3) as conn:
                conn.sendall(("GET / HTTP/1.1\r\n" + headers + "\r\n").encode())
                self.assertIn(b" 403 ", conn.recv(4096).split(b"\r\n")[0])

    def test_cli_check_outputs_real_asset_hashes_and_closes_listener(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        result = subprocess.run([sys.executable, "-S", str(ROOT / "tools/host_diagnostic.py"),
                                 "--check", "--port", str(port)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads(result.stdout)
        for route, name in [("/index.html", "index.html"), ("/diagnostic.js", "diagnostic.js")]:
            self.assertEqual(manifest["assets"][route]["sha256"],
                             hashlib.sha256((ROOT / "diagnostics/browser" / name).read_bytes()).hexdigest())
        with socket.socket() as sock:
            self.assertNotEqual(sock.connect_ex(("127.0.0.1", port)), 0)

    def test_cli_rejects_wildcard_and_privileged_ports(self):
        tool = str(ROOT / "tools/host_diagnostic.py")
        for options in [["--bind", "0.0.0.0"], ["--port", "80"], ["--port", "65536"]]:
            result = subprocess.run([sys.executable, "-S", tool, "--check"] + options,
                                    text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("Ready", result.stdout)


if __name__ == "__main__":
    unittest.main()
