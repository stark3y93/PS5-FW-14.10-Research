"""Bridge state and real loopback protocol safety, without PS5 operations."""
import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
from ps5fwlab import bridge


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = bridge.BridgeState(Path(self.tmp.name) / "run")

    def register(self):
        return self.state.register(self.state.pair_key, {"firmware": "14.10", "user_agent": "fixture PS5", "secure_context": False})

    def test_wrong_pair_and_session_rejected(self):
        with self.assertRaises(ValueError): self.state.register("wrong", {})
        with self.assertRaises(ValueError): self.state.client("wrong")

    def test_only_fixed_tasks_can_be_scheduled_and_completed(self):
        reg = self.register()
        with self.assertRaises(ValueError): self.state.schedule(reg["client_id"], "eval")
        job = self.state.schedule(reg["client_id"], "surface")
        polled = self.state.poll(reg["token"])
        self.assertEqual(polled["id"], job["id"])
        result = {"test_id": "surface.Promise", "gate": "CONFIRMED AVAILABLE", "observed": True,
                  "error": "", "scope": "current page", "confidence": "AUTOMATED OBSERVATION"}
        self.state.submit(reg["token"], job["id"], [result])
        self.assertEqual(self.state.snapshot()["jobs"][0]["status"], "partial")
        self.assertIn("surface.Map", self.state.snapshot()["jobs"][0]["missing_tests"])
        self.assertTrue(list(self.state.directory.glob("report-*.json")))
        exports = json.dumps(self.state.snapshot())
        self.assertNotIn(reg["token"], exports)
        self.assertNotIn(self.state.pair_key, exports)
        self.assertIn("expected", exports)

    def test_job_cannot_be_claimed_by_another_client_or_replayed(self):
        a, b = self.register(), self.register()
        job = self.state.schedule(a["client_id"], "surface")
        self.state.poll(a["token"])
        with self.assertRaises(ValueError): self.state.submit(b["token"], job["id"], [])
        self.state.submit(a["token"], job["id"], [])
        with self.assertRaises(ValueError): self.state.submit(a["token"], job["id"], [])

    def test_unknown_and_privilege_claims_rejected(self):
        reg = self.register(); job = self.state.schedule(reg["client_id"], "surface"); self.state.poll(reg["token"])
        for value in [{"test_id": "kernel.execution"}, {"test_id": "surface.Promise", "gate": "JAILBROKEN"},
                      {"test_id": "surface.Promise", "kernel_execution": True}]:
            with self.assertRaises(ValueError): self.state.submit(reg["token"], job["id"], [value])

    def test_empty_manual_batches_cannot_grow_evidence_and_reports(self):
        reg=self.register(); before=len(list(self.state.directory.iterdir()))
        with self.assertRaises(ValueError): self.state.manual(reg["token"],[])
        self.assertEqual(len(list(self.state.directory.iterdir())),before)

    def test_run_disk_budget_stops_writes_without_overwriting_evidence(self):
        reg=self.register(); before=(self.state.directory/'events.ndjson').read_bytes()
        self.state.disk_budget=1
        with self.assertRaises(ValueError): self.state.schedule(reg["client_id"], 'surface')
        self.assertEqual((self.state.directory/'events.ndjson').read_bytes(),before)

    def test_expired_job_and_offline_client_are_explicit(self):
        reg = self.register(); job = self.state.schedule(reg["client_id"], "surface")
        self.state.poll(reg["token"])
        self.state.jobs[job["id"]]["deadline"] = 0
        self.state.clients[reg["client_id"]]["seen"] = 0
        snap = self.state.snapshot()
        self.assertEqual(snap["jobs"][0]["status"], "timeout")
        self.assertFalse(snap["clients"][0]["online"])

    def test_raw_evidence_is_retained_and_markdown_is_escaped(self):
        reg = self.register(); job = self.state.schedule(reg["client_id"], "surface"); self.state.poll(reg["token"])
        row = {"test_id": "surface.Promise", "gate": "INCONCLUSIVE", "observed": "![x](evil)|<script>",
               "error": "error\n#fake", "scope": "fixture", "confidence": "AUTOMATED OBSERVATION"}
        self.state.submit(reg["token"], job["id"], [row])
        self.assertTrue((self.state.directory / "events.ndjson").is_file())
        md = bridge.render_matrix(self.state.snapshot())
        self.assertNotIn("![x]", md); self.assertNotIn("<script>", md)
        self.assertIn("evidence", json.dumps(self.state.snapshot()))

    def test_http_protocol_requires_auth_origin_and_exact_routes(self):
        servers = bridge.make_servers("127.0.0.1", 0, 0, self.state)
        for s in servers:
            threading.Thread(target=s.serve_forever, daemon=True).start()
        self.addCleanup(lambda: [(s.shutdown(), s.server_close()) for s in servers])
        s = servers[0]
        def request(method, path, obj=None, auth=None, origin=None):
            c = http.client.HTTPConnection(*s.server_address, timeout=3)
            headers = {"Content-Type": "application/json"}
            if auth: headers["Authorization"] = "Bearer " + auth
            if origin: headers["Origin"] = origin
            c.request(method, path, json.dumps(obj) if obj is not None else None, headers)
            r = c.getresponse(); data = r.read(); code = r.status; c.close(); return code, data
        self.assertEqual(request("GET", "/api/state")[0], 403)
        self.assertEqual(request("GET", "/../README.md")[0], 404)
        self.assertEqual(request("POST", "/api/register", {"pair_key": self.state.pair_key, "info": {}}, origin="http://evil.invalid")[0], 403)
        code, data = request("POST", "/api/register", {"pair_key": self.state.pair_key, "info": {"firmware": "14.10", "user_agent": "fixture", "secure_context": False}}, origin=s.origin)
        self.assertEqual(code, 200, data)
        self.assertEqual(request("GET", "/api/state", auth=self.state.admin_key)[0], 200)

    def test_controlled_second_origin_has_only_explicit_cors_allow(self):
        servers = bridge.make_servers("127.0.0.1", 0, 0, self.state)
        for s in servers: threading.Thread(target=s.serve_forever, daemon=True).start()
        self.addCleanup(lambda: [(s.shutdown(), s.server_close()) for s in servers])
        for path in ("/net/cors-allow", "/net/cors-deny"):
            c = http.client.HTTPConnection(*servers[1].server_address, timeout=3)
            c.request("GET", path, headers={"Origin": servers[0].origin})
            r=c.getresponse(); body=r.read();self.assertEqual(r.status,200,body)
            self.assertEqual(r.getheader("Access-Control-Allow-Origin"),servers[0].origin if path.endswith("allow") else None)
            c.close()


if __name__ == "__main__": unittest.main()
