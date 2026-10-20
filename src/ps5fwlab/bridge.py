"""Authenticated, bounded LAN research bridge. No console commands or exploits."""
import argparse
import base64
import hashlib
import hmac
import json
import re
import secrets
import socket
import ssl
import struct
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .browser_evidence import _cell
from .diagnostic_host import validate_bind, CSP as PASSIVE_CSP

ROOT = Path(__file__).resolve().parents[2]
TEXT = b"PS5 capability suite: harmless synthetic text.\n"
GATES = ("CONFIRMED AVAILABLE", "CONFIRMED BLOCKED OR UNAVAILABLE", "INCONCLUSIVE",
         "REQUIRES HTTPS", "REQUIRES USER INTERACTION", "NOT TESTABLE FROM A NORMAL WEBPAGE")
TASKS = {
    "surface": "Promise Map Set Symbol BigInt ArrayBuffer Uint8Array TextEncoder FontFace TransformStream fontSet cssGrid cssFontFamily WebAssembly clipboard fileInput fileSystem fileAPIs devices isolation permissions",
    "storage": "local session indexedDB estimate reload cleanup",
    "network": "fetchGET fetchPOST xhrGET xhrPOST cors websocket eventSource streaming timeout failure",
    "security": "context permissions wasm worker serviceWorker crypto sandbox csp",
    "rendering": "language buffer canvas webgl timing errors",
    "manual": "downloadLink txtDownload attribute blobDownload fileOpen fileUpload popup navigation storageCleanup",
}
CATALOG = {task + "." + name: {"task": task, "expected": {
    "surface": "Read API availability only; absence is limited to this page/context.",
    "storage": "Write/read <=4 KiB of suite-owned synthetic data; report errors and prior sentinel.",
    "network": "Exchange a bounded synthetic response with the local controlled endpoints.",
    "security": "Observe a standard API or controlled policy without requesting privileges.",
    "rendering": "Complete a small bounded local operation without resource stress.",
    "manual": "Explicit local gesture and observer confirmation; request alone does not prove completion.",
}[task]} for task, names in TASKS.items() for name in names.split()}
EXPECTED = {
    "storage.local": "Write/read one suite-owned localStorage sentinel; preserve ownership collisions.",
    "storage.session": "Write/read one suite-owned sessionStorage sentinel; preserve ownership collisions.",
    "storage.indexedDB": "Open only the synthetic database, read/write its sentinel and close the transaction.",
    "storage.estimate": "Write/read/remove 2048 ASCII characters (<=4096 UTF-16 payload bytes); optionally read origin quota estimate.",
    "storage.reload": "Find a known synthetic sentinel from a different page instance, not a same-page rerun.",
    "storage.cleanup": "Retain markers until the user explicitly requests owned-data cleanup.",
    "network.fetchGET": "fetch GET returns the same-origin synthetic marker.",
    "network.fetchPOST": "fetch POST sends and returns the same-origin synthetic marker.",
    "network.xhrGET": "XHR GET returns the same-origin synthetic marker.",
    "network.xhrPOST": "XHR POST returns the synthetic marker and POST method.",
    "network.cors": "Explicit-allow second-origin control is readable; no-header control is not readable.",
    "network.websocket": "Authenticated bounded WebSocket exchange returns one synthetic marker.",
    "network.eventSource": "Receive one synthetic SSE message then close the connection.",
    "network.streaming": "Read one bounded response chunk using ReadableStream.getReader then cancel.",
    "network.timeout": "The intentionally delayed local endpoint triggers the 100ms XHR deadline.",
    "network.failure": "The controlled connection-close endpoint produces an explicit network error.",
    "security.context": "Observe current secure-context and cross-origin-isolation flags; HTTP LAN and loopback can differ.",
    "security.permissions": "Query geolocation permission state without requesting permission or position.",
    "security.wasm": "If exposed, validate an 8-byte empty module; no permanent disablement inference.",
    "security.worker": "A temporary Blob worker sends one marker, is terminated, and its URL revoked.",
    "security.serviceWorker": "Register/unregister only the isolated suite scope, without caches or a fetch handler.",
    "security.crypto": "SHA-256 of 3 synthetic bytes returns a 32-byte digest.",
    "security.sandbox": "Controlled allow-scripts sandbox has an opaque message origin and denies parent DOM access.",
    "security.csp": "The static control loads while its explicitly forbidden inline script does not execute.",
    "rendering.language": "Small Map/Set/Symbol/BigInt operations and Promise availability behave as reported.",
    "rendering.buffer": "One 256 KiB buffer supports first/last typed-array byte readback.",
    "rendering.canvas": "A 16x16 canvas returns the expected one-pixel red readback.",
    "rendering.webgl": "Create/clear one 16x16 WebGL context and release it when supported.",
    "rendering.timing": "Time 10000 integer additions; do not infer a firmware or performance guarantee.",
    "rendering.errors": "Catch a synthetic Error and record its name/message without throwing an unhandled exception.",
}
for _id, _item in CATALOG.items():
    if _id in EXPECTED: _item['expected'] = EXPECTED[_id]
    elif _item['task'] == 'surface': _item['expected'] = 'Check ' + _id.split('.')[1] + ' exposure in this page without privileged operations; availability is not exploitation.'
    elif _item['task'] == 'manual': _item['expected'] = 'Observe ' + _id.split('.')[1] + ' only through its explicit local control; preserve requested versus observed completion.'


def utc():
    return datetime.now(timezone.utc).isoformat()


def bounded_json(raw):
    if len(raw) > 65536:
        raise ValueError("JSON body exceeds 64 KiB")
    def pairs(items):
        d = {}
        for k, v in items:
            if k in d: raise ValueError("duplicate JSON key")
            d[k] = v
        return d
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite number")))
    def depth(x, n=0):
        if n > 8: raise ValueError("JSON nesting too deep")
        if isinstance(x, dict):
            for v in x.values(): depth(v, n + 1)
        elif isinstance(x, list):
            for v in x: depth(v, n + 1)
    depth(value)
    if not isinstance(value, dict): raise ValueError("JSON object required")
    return value


class BridgeState:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=False)
        self.pair_key = secrets.token_hex(8)
        self.admin_key = secrets.token_urlsafe(24)
        self.clients, self.jobs, self.results = {}, {}, []
        self.lock = threading.RLock()
        self.seq = 0
        self.disk_budget = 32 * 1024 * 1024
        self.written_bytes = 0
        self.started = utc()
        self.assets = {}

    def event(self, kind, data):
        next_sequence = self.seq + 1
        record = {"sequence": next_sequence, "server_time": utc(), "kind": kind, "data": data}
        raw = (json.dumps(record, ensure_ascii=True, allow_nan=False) + "\n").encode()
        self.reserve(len(raw))
        with (self.directory / "events.ndjson").open("ab") as f: f.write(raw)
        self.seq = next_sequence
        self.written_bytes += len(raw)
        return {"file": "events.ndjson", "line": self.seq, "sha256": hashlib.sha256(raw).hexdigest()}

    def reserve(self, count):
        if self.written_bytes + count > self.disk_budget:
            raise ValueError("32 MiB run evidence budget reached; export existing state and start a new run")

    def register(self, pair_key, info, context=None):
        with self.lock:
            if not isinstance(pair_key, str) or not hmac.compare_digest(pair_key, self.pair_key): raise ValueError("pairing rejected")
            if len(self.clients) >= 8: raise ValueError("8-client run limit reached; restart for a new run")
            if (not isinstance(info, dict) or set(info) != {"firmware", "user_agent", "secure_context"}
                    or not isinstance(info["firmware"], str) or not re.fullmatch(r"\d{1,2}\.\d{2}", info["firmware"])
                    or not isinstance(info["user_agent"], str) or len(info["user_agent"]) > 1024
                    or type(info["secure_context"]) is not bool): raise ValueError("invalid identity fields")
            ident, token = secrets.token_hex(6), secrets.token_urlsafe(24)
            context = context or {"origin": "offline model", "transport": "unknown"}
            evidence = self.event("registration", {"client_id": ident, "info": info, "context": context, "identity_authenticated": False})
            self.clients[ident] = {"client_id": ident, "token": token, "info": info, "context": context, "seen": time.monotonic(), "last_seen": utc(), "evidence": evidence}
            return {"client_id": ident, "token": token}

    def client(self, token):
        if not isinstance(token, str): raise ValueError("session rejected")
        with self.lock:
            for client in self.clients.values():
                if hmac.compare_digest(token, client["token"]): return client
        raise ValueError("session rejected")

    def heartbeat(self, token):
        with self.lock:
            c = self.client(token); c.update(seen=time.monotonic(), last_seen=utc())
            return {"ok": True, "server_time": utc()}

    def expire(self):
        now = time.monotonic()
        for job in self.jobs.values():
            if job["status"] in ("queued", "running") and now > job["deadline"]:
                job.update(status="timeout", error="No complete result before 60-second deadline; cause unknown")
                try: self.event("timeout", {k: v for k, v in job.items() if k != "deadline"})
                except ValueError: job["evidence_error"] = "Disk budget reached; timeout retained in memory only"

    def schedule(self, client_id, task):
        with self.lock:
            self.expire()
            if client_id not in self.clients or task not in TASKS or task == "manual": raise ValueError("task/client not allowed")
            if len(self.jobs) >= 128: raise ValueError("128-job run limit reached")
            if any(j["client_id"] == client_id and j["status"] in ("queued", "running") for j in self.jobs.values()): raise ValueError("client already has a pending task")
            job = {"id": secrets.token_hex(8), "client_id": client_id, "task": task, "status": "queued", "created_at": utc(), "deadline": time.monotonic() + 60}
            self.event("scheduled", {k: v for k, v in job.items() if k != "deadline"})
            self.jobs[job["id"]] = job
            return {k: v for k, v in job.items() if k != "deadline"}

    def poll(self, token):
        with self.lock:
            c = self.client(token); self.expire()
            for j in self.jobs.values():
                if j["client_id"] == c["client_id"] and j["status"] == "queued":
                    j.update(status="running", started_at=utc(), deadline=time.monotonic() + 60)
                    return {"id": j["id"], "task": j["task"], "timeout_ms": 30000}
            return None

    def _rows(self, rows, task):
        if not isinstance(rows, list) or len(rows) > 64: raise ValueError("result array exceeds limit")
        clean, seen = [], set()
        for r in rows:
            if not isinstance(r, dict) or set(r) != {"test_id", "gate", "observed", "error", "scope", "confidence"}: raise ValueError("unexpected result fields")
            ident = r["test_id"]
            if not isinstance(ident, str) or ident not in CATALOG or CATALOG[ident]["task"] != task or ident in seen: raise ValueError("test not in scheduled catalog or duplicate")
            if r["gate"] not in GATES or r["confidence"] not in ("AUTOMATED OBSERVATION", "USER OBSERVATION"): raise ValueError("unsupported classification")
            if any(not isinstance(r[k], str) or len(r[k]) > 512 for k in ("error", "scope")): raise ValueError("invalid error/scope")
            if len(json.dumps(r["observed"], allow_nan=False)) > 2048: raise ValueError("observation too large")
            seen.add(ident); clean.append(dict(r, expected=CATALOG[ident]["expected"]))
        return clean

    def submit(self, token, job_id, rows):
        with self.lock:
            c = self.client(token); self.expire()
            j = self.jobs.get(job_id)
            if not j or j["client_id"] != c["client_id"] or j["status"] != "running": raise ValueError("job is not running for this client (expired/replayed/unknown)")
            clean = self._rows(rows, j["task"])
            self._retain(c, clean, job_id)
            missing = sorted(k for k, v in CATALOG.items() if v["task"] == j["task"] and k not in {r["test_id"] for r in clean})
            j.update(status="complete" if not missing else "partial" if clean else "inconclusive", completed_at=utc(), missing_tests=missing)
            self.write_report()

    def manual(self, token, rows):
        with self.lock:
            c = self.client(token); clean = self._rows(rows, "manual")
            if not clean: raise ValueError("empty manual result batch rejected")
            self._retain(c, clean, "explicit-client-action")
            self.write_report()

    def _retain(self, client, rows, job_id):
        if len(self.results) + len(rows) > 2048: raise ValueError("2048-result run limit reached")
        evidence = self.event("results", {"client_id": client["client_id"], "job_id": job_id, "results": rows})
        for r in rows:
            self.results.append(dict(r, client_id=client["client_id"], job_id=job_id, received_at=utc(), evidence=evidence,
                                     context=client["context"], identity_authenticated=False,
                                     confidence_level="MEDIUM" if r['confidence']=='AUTOMATED OBSERVATION' and r['gate'] in GATES[:2] else "LOW",
                                     scope_kind="security-context-specific" if r['test_id'].startswith('security.') or r['test_id'] in ('network.cors','surface.clipboard','surface.fileSystem','surface.isolation') else "browser/context observation; underlying cause not established"))

    def snapshot(self):
        with self.lock:
            self.expire()
            return {"schema": "ps5-browser-bridge/1", "started_at": self.started, "server_time": utc(), "assets": self.assets,
                    "clients": [{"client_id": c["client_id"], "info": c["info"], "context": c["context"], "last_seen": c["last_seen"], "online": time.monotonic() - c["seen"] < 30, "evidence": c["evidence"]} for c in self.clients.values()],
                    "jobs": [{k: v for k, v in j.items() if k != "deadline"} for j in self.jobs.values()],
                    "results": list(self.results), "limits": ["Authenticated bridge session is not authenticated hardware/firmware", "Every observation is limited to its page, context and test", "No exploit or privileged-access verdict"]}

    def write_report(self):
        report = self.snapshot(); name = "report-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + str(self.seq)
        files = [(".json", (json.dumps(report, indent=2) + "\n").encode()), (".md", (render_matrix(report) + "\n").encode())]
        self.reserve(sum(len(data) for _, data in files))
        for suffix, data in files:
            with (self.directory / (name + suffix)).open("xb") as f: f.write(data)
            self.written_bytes += len(data)


def render_matrix(report):
    lines = ["# Browser security gate report", "", "Observations do not establish a vulnerability or system access.", "",
             "| Test | Gate | Expected | Observed | Error | Scope | Confidence | Evidence |", "|---|---|---|---|---|---|---|---|"]
    for r in report["results"]:
        vals = [r["test_id"], r["gate"], r["expected"], json.dumps(r["observed"], ensure_ascii=True), r["error"], r["scope"]+' / '+r['scope_kind'], r['confidence_level']+' / '+r["confidence"], json.dumps(r["evidence"])]
        lines.append("| " + " | ".join(_cell(v) for v in vals) + " |")
    lines.extend(["", "## Jobs", ""])
    for j in report["jobs"]: lines.append("- " + _cell(j["id"] + ": " + j["task"] + " / " + j["status"] + " " + j.get("error", "")))
    lines.extend(["", "## Limits", ""] + ["- " + s for s in report["limits"]])
    return "\n".join(lines)


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False
    def process_request(self, request, address):
        if not self.slots.acquire(False): request.close(); return
        super().process_request(request, address)
    def process_request_thread(self, request, address):
        try: super().process_request_thread(request, address)
        finally: self.slots.release()
    def handle_error(self, request, address): pass


class Handler(BaseHTTPRequestHandler):
    server_version = "PS5ResearchBridge/1"
    sys_version = ""
    def setup(self):
        super().setup(); self.connection.settimeout(4)
    def log_message(self, *args): pass
    def reply(self, code, value, mime="application/json; charset=utf-8", extra=None):
        raw = value if isinstance(value, bytes) else json.dumps(value).encode()
        self.send_response(code)
        for k, v in {"Content-Type": mime, "Content-Length": str(len(raw)), "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer", "Connection": "close", **(extra or {})}.items(): self.send_header(k, v)
        self.end_headers(); self.close_connection = True
        if self.command != "HEAD": self.wfile.write(raw)
    def token(self):
        value = self.headers.get("Authorization", "")
        return value[7:] if value.startswith("Bearer ") else ""
    def admin(self):
        return self.client_address[0] in ("127.0.0.1", self.server.server_address[0]) and hmac.compare_digest(self.token(), self.server.state.admin_key)
    def valid(self, mutation=False):
        if self.headers.get_all("Host", []) != [self.server.authority]: return False
        origin = self.headers.get_all("Origin", [])
        cross_control = self.command == "GET" and self.requestline.split()[1] in ("/net/cors-allow", "/net/cors-deny")
        if origin and origin != [self.server.origin] and not (cross_control and origin == [self.server.other_origin]): return False
        if mutation and origin != [self.server.origin]: return False
        return True
    def do_GET(self):
        if not self.valid(): self.reply(403, {"error": "Host/Origin rejected"}); return
        path = self.requestline.split()[1]
        state = self.server.state
        try:
            if path == "/api/state" or path in ("/api/export.json", "/api/export.md"):
                if self.server.secondary or not self.admin(): self.reply(403, {"error": "PC dashboard authentication required"}); return
                snap = state.snapshot()
                if path.endswith(".md"): self.reply(200, render_matrix(snap).encode(), "text/markdown; charset=utf-8")
                else: self.reply(200, snap)
            elif path == "/api/poll" and not self.server.secondary:
                self.reply(200, {"job": state.poll(self.token())})
            elif path == "/config" and not self.server.secondary:
                self.reply(200, {"catalog": CATALOG, "tasks": [x for x in TASKS if x != "manual"], "secondary_origin": self.server.other_origin, "text": TEXT.decode(), "transport": self.server.scheme})
            elif path in self.server.assets and not self.server.secondary:
                data, mime = self.server.assets[path]
                csp = "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self' " + self.server.other_origin + " " + self.server.origin.replace("http", "ws", 1) + "; frame-src 'self'; worker-src 'self' blob:; img-src 'self'; object-src 'none'; base-uri 'none'; form-action 'none'"
                self.reply(200, data, mime, {"Content-Security-Policy": PASSIVE_CSP if path.startswith('/passive/') else csp})
            elif path in ("/files/sample.txt", "/files/download.txt") and not self.server.secondary:
                self.reply(200, TEXT, "text/plain; charset=utf-8", {"Content-Disposition": ('attachment; filename="ps5-synthetic.txt"' if path.endswith("download.txt") else "inline")})
            elif path in ("/net/echo", "/net/cors-allow", "/net/cors-deny"):
                headers = {"Access-Control-Allow-Origin": self.server.other_origin, "Vary": "Origin"} if path == "/net/cors-allow" else {}
                self.reply(200, {"marker": "PS5-BRIDGE-SYNTHETIC", "method": "GET"}, extra=headers)
            elif path == "/net/events":
                self.reply(200, b'data: PS5-BRIDGE-SYNTHETIC\n\n', "text/event-stream; charset=utf-8")
            elif path == "/net/stream":
                self.reply(200, TEXT, "text/plain; charset=utf-8")
            elif path == "/net/slow":
                time.sleep(1); self.reply(200, {"marker": "late synthetic response"})
            elif path == "/net/closed":
                self.connection.shutdown(socket.SHUT_RDWR); self.close_connection = True
            elif path == "/net/ws" and not self.server.secondary:
                self.websocket()
            elif path == "/frames/sandbox" and not self.server.secondary:
                self.reply(200, b'<script>parent.postMessage({bridge:"sandbox-child"},"*")</script>', "text/html; charset=utf-8", {"Content-Security-Policy": "default-src 'none'; script-src 'unsafe-inline'"})
            elif path == "/frames/csp" and not self.server.secondary:
                self.reply(200, b'<div id="control">loaded</div><script>window.bridgeExecuted=true;</script>', "text/html; charset=utf-8", {"Content-Security-Policy": "default-src 'none'; script-src 'none'"})
            elif path in ("/manual/popup", "/manual/navigation") and not self.server.secondary:
                self.reply(200, b'<h1>Harmless synthetic navigation page</h1><p>Use normal Back/Close to return.</p>', "text/html; charset=utf-8")
            else: self.reply(404, {"error": "route not allowed"})
        except (ValueError, KeyError): self.reply(400, {"error": "request or session rejected"})
        except (OSError, TimeoutError): self.close_connection = True
    do_HEAD = do_GET

    def do_POST(self):
        if self.server.secondary or not self.valid(True): self.reply(403, {"error": "mutation origin rejected"}); return
        state = self.server.state
        try:
            if self.headers.get("Transfer-Encoding") or len(self.headers.get_all("Content-Length", [])) != 1: raise ValueError("length required")
            size = int(self.headers["Content-Length"])
            if not 0 < size <= 65536 or self.headers.get("Content-Type", "").split(";")[0] != "application/json": raise ValueError("body invalid")
            now = time.monotonic(); key = self.client_address[0]
            with state.lock:
                times = [t for t in self.server.rates.get(key, []) if now - t < 60]
                if len(times) >= 90: self.reply(429, {"error": "request limit; wait one minute"}); return
                self.server.rates[key] = times + [now]
            raw = self.rfile.read(size)
            if len(raw) != size: raise ValueError("truncated body")
            data = bounded_json(raw); path = self.requestline.split()[1]
            if path == "/api/register" and set(data) == {"pair_key", "info"}:
                self.reply(200, state.register(data["pair_key"], data["info"], {"origin": self.server.origin, "transport": self.server.scheme}))
            elif path == "/api/heartbeat" and data == {}:
                self.reply(200, state.heartbeat(self.token()))
            elif path == "/api/start" and set(data) == {"task"}:
                c = state.client(self.token()); self.reply(200, state.schedule(c["client_id"], data["task"]))
            elif path == "/api/schedule" and self.admin() and set(data) == {"client_id", "task"}:
                self.reply(200, state.schedule(data["client_id"], data["task"]))
            elif path == "/api/results" and set(data) == {"job_id", "results"}:
                state.submit(self.token(), data["job_id"], data["results"]); self.reply(200, {"ok": True})
            elif path == "/api/manual" and set(data) == {"results"}:
                state.manual(self.token(), data["results"]); self.reply(200, {"ok": True})
            elif path == "/net/echo" and data == {"marker": "PS5-BRIDGE-SYNTHETIC"}:
                self.reply(200, {"marker": "PS5-BRIDGE-SYNTHETIC", "method": "POST"})
            else: self.reply(400, {"error": "operation not allowed"})
        except (ValueError, KeyError, TypeError, RecursionError, UnicodeError) as exc: self.reply(400, {"error": str(exc)[:220] + "; preserve client JSON if upload failed"})
        except (OSError, TimeoutError): self.close_connection = True

    def websocket(self):
        if self.command != "GET" or self.headers.get("Origin") != self.server.origin: self.reply(403, {}); return
        try:
            key = self.headers.get("Sec-WebSocket-Key", "")
            if len(base64.b64decode(key, validate=True)) != 16 or self.headers.get("Sec-WebSocket-Version") != "13" or self.headers.get("Upgrade", "").lower() != "websocket" or 'upgrade' not in self.headers.get('Connection','').lower().replace(' ','').split(','): raise ValueError()
            accept = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
            self.send_response(101); self.send_header("Upgrade", "websocket"); self.send_header("Connection", "Upgrade"); self.send_header("Sec-WebSocket-Accept", accept); self.end_headers(); self.wfile.flush()
            head = self.rfile.read(2)
            if len(head) != 2 or head[0] != 0x81 or not head[1] & 0x80: return
            n = head[1] & 127
            if n == 126: n = struct.unpack("!H", self.rfile.read(2))[0]
            if n > 1024 or n == 127: return
            mask, payload = self.rfile.read(4), self.rfile.read(n)
            if len(mask) != 4 or len(payload) != n: return
            data = bounded_json(bytes(v ^ mask[i % 4] for i, v in enumerate(payload)))
            if set(data) != {"token", "marker"} or data["marker"] != "PS5-BRIDGE-SYNTHETIC": return
            self.server.state.client(data["token"])
            out = b'{"marker":"PS5-BRIDGE-SYNTHETIC"}'
            self.wfile.write(bytes([0x81, len(out)]) + out + b'\x88\x02\x03\xe8'); self.wfile.flush()
        except (ValueError, OSError, struct.error): pass
        finally: self.close_connection = True


def make_servers(address, port, secondary_port, state, tls=None):
    address = validate_bind(address)
    for p in (port, secondary_port):
        if type(p) is not int or not (p == 0 or 1024 <= p <= 65535): raise ValueError("ports must be 1024..65535")
    assets = {}
    for name, mime in (("index.html", "text/html; charset=utf-8"), ("dashboard.html", "text/html; charset=utf-8"), ("client.js", "text/javascript; charset=utf-8"), ("suite.js", "text/javascript; charset=utf-8"), ("dashboard.js", "text/javascript; charset=utf-8"), ("style.css", "text/css; charset=utf-8"), ("sw.js", "text/javascript; charset=utf-8")):
        path = ROOT / "diagnostics" / "bridge" / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 262144: raise ValueError("missing/oversized bridge asset " + name)
        assets["/bridge/" + name] = (path.read_bytes(), mime)
    assets["/"] = assets["/bridge/index.html"]
    assets["/dashboard"] = assets["/bridge/dashboard.html"]
    for name, mime in (("index.html", "text/html; charset=utf-8"), ("diagnostic.js", "text/javascript; charset=utf-8")):
        path = ROOT / "diagnostics" / "browser" / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 262144: raise ValueError("passive diagnostic asset unavailable")
        assets["/passive/" + name] = (path.read_bytes(), mime)
    assets['/passive/'] = assets['/passive/index.html']
    state.assets = {k: hashlib.sha256(v[0]).hexdigest() for k, v in assets.items()}
    servers = []
    try:
        for p in (port, secondary_port):
            s = Server((address, p), Handler); servers.append(s)
            s.slots = threading.BoundedSemaphore(16); s.state = state; s.assets = assets; s.rates = {}
            s.scheme = "https" if tls else "http"
            s.authority = address + ":" + str(s.server_port); s.origin = s.scheme + "://" + s.authority
            if tls: s.socket = tls.wrap_socket(s.socket, server_side=True, do_handshake_on_connect=False)
        for i, s in enumerate(servers): s.secondary = bool(i); s.other_origin = servers[1 - i].origin
        return servers
    except Exception:
        for s in servers: s.server_close()
        raise


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bind", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8768); p.add_argument("--secondary-port", type=int, default=8769)
    p.add_argument("--output-base", type=Path, default=ROOT / "derived")
    p.add_argument("--tls-cert", type=Path); p.add_argument("--tls-key", type=Path)
    p.add_argument("--check", action="store_true")
    a = p.parse_args(argv)
    if bool(a.tls_cert) != bool(a.tls_key): p.error("TLS requires both existing certificate and key; no trust is installed")
    if a.port == a.secondary_port or any(not 1024 <= n <= 65535 for n in (a.port, a.secondary_port)): p.error("choose distinct high ports")
    servers = []
    try:
        validate_bind(a.bind)
        tls = None
        if a.tls_cert:
            tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); tls.minimum_version = ssl.TLSVersion.TLSv1_2; tls.load_cert_chain(a.tls_cert, a.tls_key)
        state = BridgeState(a.output_base / ("bridge-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(3)))
        servers = make_servers(a.bind, a.port, a.secondary_port, state, tls)
        print("Client:", servers[0].origin + "/", "\nDashboard (PC only):", servers[0].origin + "/dashboard", "\nEvidence:", state.directory, flush=True)
        if a.check: return 0
        print("Pairing key:", state.pair_key, "\nPC dashboard key:", state.admin_key, "\nKeep keys local. HTTP is not encrypted. Stop with Ctrl+C.", flush=True)
        for s in servers: threading.Thread(target=s.serve_forever, daemon=True).start()
        while True: time.sleep(1)
    except KeyboardInterrupt: return 0
    except (OSError, ValueError) as exc: p.error("bridge not started: " + str(exc))
    finally:
        for s in servers: s.server_close()
    return 0


if __name__ == "__main__": raise SystemExit(main())
