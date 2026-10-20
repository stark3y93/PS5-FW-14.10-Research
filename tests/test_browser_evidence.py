"""Capability observations cannot authenticate a vulnerability or privilege."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ps5fwlab import browser_evidence as be

ROOT = Path(__file__).resolve().parents[1]


def fixture(**changes):
    value = {"schema": "ps5-browser-diagnostic/1", "diagnostic_version": "1.0",
             "status": "complete", "firmware_label": "14.10", "captured_at": "2026-10-20T00:00:00Z",
             "user_agent": "Mozilla/5.0 (PlayStation; PlayStation 5/14.10)",
             "features": {"FontFace": True, "fontSet": True, "Promise": True}}
    value.update(changes)
    return value


class BrowserEvidenceTests(unittest.TestCase):
    def analyze(self, values, target="14.10"):
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for i, value in enumerate(values):
                p = Path(directory) / (str(i) + ".json")
                p.write_text(json.dumps(value), encoding="utf-8")
                paths.append(p)
            return be.analyze_diagnostics(paths, target)

    def test_complete_capture_still_cannot_verify_target_or_privilege(self):
        report = self.analyze([fixture()])
        self.assertEqual(report["records"][0]["status"], "complete")
        self.assertFalse(report["target_authenticated"])
        self.assertEqual(report["vulnerability_verdict"], "INSUFFICIENT EVIDENCE")
        self.assertEqual(report["contradictions"], [])
        self.assertTrue(all(x["status"] == "UNPROVEN" for x in report["boundaries"] if x["stage"] != "browser_page"))

    def test_same_label_opposite_capability_is_observation_conflict(self):
        changed = fixture(features={"FontFace": False, "fontSet": True, "Promise": True})
        report = self.analyze([fixture(), changed])
        self.assertEqual(len(report["contradictions"]), 1)
        self.assertEqual(report["contradictions"][0]["feature"], "FontFace")
        self.assertEqual(report["contradictions"][0]["evidence"][0]["pointer"], "/features/FontFace")

    def test_different_firmware_is_not_a_contradiction(self):
        report = self.analyze([fixture(), fixture(firmware_label="13.60", features={"FontFace": False})])
        self.assertEqual(report["contradictions"], [])
        self.assertIn("firmware-label-mismatch", report["records"][1]["warnings"])

    def test_incomplete_record_does_not_contradict_complete(self):
        report = self.analyze([fixture(), fixture(status="started", features={"FontFace": False})])
        self.assertEqual(report["contradictions"], [])
        self.assertEqual(report["records"][1]["status"], "incomplete")

    def test_unknown_feature_is_not_false_and_labels_are_not_ua_proof(self):
        report = self.analyze([fixture(features={"FontFace": "error"}), fixture()])
        self.assertEqual(report["contradictions"], [])
        report = self.analyze([fixture(user_agent="PlayStation 5/13.60")])
        self.assertIn("ua-firmware-disagrees", report["records"][0]["warnings"])

    def test_privilege_and_vulnerability_claims_are_rejected(self):
        report = self.analyze([fixture(kernel_execution=True, vulnerability="VERIFIED", target_authenticated=True)])
        self.assertIn("unsupported-claim-fields", report["records"][0]["warnings"])
        self.assertFalse(report["target_authenticated"])

    def test_provenance_uses_exact_bytes_and_json_pointer(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "record.json"
            raw = json.dumps(fixture()).encode()
            p.write_bytes(raw)
            result = be.analyze_diagnostics([p], "14.10")["records"][0]
            self.assertEqual(result["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(result["evidence"]["pointer"], "/features")

    def test_invalid_inputs_fail_closed(self):
        for value in [[], {}, fixture(features=[]), fixture(features={"FontFace": 1}),
                      fixture(schema="other"), fixture(firmware_label="14"), fixture(status=True)]:
            with self.subTest(value=value):
                self.assertEqual(self.analyze([value])["records"][0]["status"], "invalid")

    def test_missing_malformed_duplicate_deep_oversize_records(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "bad.json"
            self.assertEqual(be.analyze_diagnostics([p])["records"][0]["status"], "invalid")
            for raw in [b"{", b'{"schema":1,"schema":2}', b"[" * 2000 + b"]" * 2000, b" " * 65537]:
                p.write_bytes(raw)
                self.assertEqual(be.analyze_diagnostics([p])["records"][0]["status"], "invalid")

    def test_duplicate_file_not_independent_evidence(self):
        report = self.analyze([fixture(), fixture()])
        self.assertEqual(len(report["records"]), 2)
        self.assertIn("duplicate-content", report["records"][1]["warnings"])

    def test_markdown_escapes_untrusted_filename(self):
        report = self.analyze([fixture()])
        report["records"][0]["file"] = "<script>|bad\n# forged"
        md = be.render_diagnostics(report)
        self.assertNotIn("<script>", md)
        self.assertNotIn("\n# forged", md)
        self.assertIn("&lt;script&gt;", md)

    def test_markdown_does_not_turn_filename_into_link_or_image(self):
        report = self.analyze([fixture()])
        report["records"][0]["file"] = "![forged](pixel.png) [click](https://invalid.example) `fake` **bold**"
        md = be.render_diagnostics(report)
        self.assertNotIn("![forged]", md)
        self.assertNotIn("[click]", md)
        self.assertNotIn("`fake`", md)
        self.assertNotIn("**bold**", md)
        self.assertIn("&#91;forged&#93;", md)

    def test_target_filter_does_not_promote_foreign_capture(self):
        report = self.analyze([fixture(firmware_label="13.60")])
        self.assertEqual(report["boundaries"][0]["status"], "UNPROVEN")

    def test_pc_preview_with_default_label_is_not_ps5_observation(self):
        report = self.analyze([fixture(user_agent="Windows Chrome/155.0")])
        self.assertIn("ua-not-ps5", report["records"][0]["warnings"])
        self.assertEqual(report["boundaries"][0]["status"], "UNPROVEN")

    def test_transform_stream_availability_is_only_a_capability(self):
        report = self.analyze([fixture(features={"TransformStream": True, "cssFontFamily": True})])
        self.assertEqual(report["records"][0]["status"], "complete")
        self.assertEqual(report["vulnerability_verdict"], "INSUFFICIENT EVIDENCE")

    def test_cli_json_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "record.json"
            out = Path(directory) / "output.json"
            p.write_text(json.dumps(fixture()), encoding="utf-8")
            cmd = [sys.executable, "-S", str(ROOT / "tools/ps5_research.py"),
                   "--browser-diagnostic", str(p), "--format", "json", "--output", str(out)]
            first = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            original = out.read_bytes()
            self.assertEqual(json.loads(original)["vulnerability_verdict"], "INSUFFICIENT EVIDENCE")
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertEqual(out.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
