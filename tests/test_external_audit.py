import tempfile
import unittest
from pathlib import Path

from tools.ps5_research import audit_external_probes, render_probe_audit


class ExternalProbeAuditTests(unittest.TestCase):
    def make_checkout(self, source, log):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        (root / "probes").mkdir()
        (root / "results").mkdir()
        (root / "probes" / "80i_claim.lua").write_text(source, encoding="utf-8")
        (root / "results" / "80i_capture.txt").write_text(log, encoding="utf-8")
        (root / "docs").mkdir()
        (root / "docs" / "PROBE_INDEX.md").write_text(
            "| 80i | thread_write | OK | Controlled write confirmed. |\n", encoding="utf-8")
        return temp, root

    def test_write_is_not_verified_without_baseline_and_readback(self):
        temp, root = self.make_checkout("expected=0xDEADBEEF", "CALLING\n")
        with temp:
            row = next(row for row in audit_external_probes(root)["probes"] if row["probe"] == "80i")
        self.assertEqual(row["status"], "CLAIMED BUT NOT DEMONSTRATED")
        self.assertFalse(row["completion_detected"])

    def test_write_requires_source_value_and_saved_readback(self):
        source = "before=0x41414141\nexpected=0xDEADBEEF\nsecond=0xCAFEBABE\n"
        log = "before=0x41414141\nCALLING\nRV=0x0 OK=true MARKER = 0xDEADBEEF\nsecond write: 0xCAFEBABE\n=== PROBE 80i COMPLETE ===\n"
        temp, root = self.make_checkout(source, log)
        with temp:
            row = next(row for row in audit_external_probes(root)["probes"] if row["probe"] == "80i")
        self.assertEqual(row["status"], "VERIFIED FROM RAW EVIDENCE")
        self.assertTrue(row["completion_detected"])
        self.assertEqual(row["capture_findings"][0]["status"], "VERIFIED FROM RAW EVIDENCE")
        self.assertFalse(audit_external_probes(root)["contradictions"])

    def test_mismatched_readback_is_contradicted(self):
        source = "before=0x41414141\nexpected=0xDEADBEEF\nsecond=0xCAFEBABE\n"
        log = "before=0x41414141\nRV=0x0 OK=true MARKER = 0x12345678\n"
        temp, root = self.make_checkout(source, log)
        with temp:
            row = next(row for row in audit_external_probes(root)["probes"] if row["probe"] == "80i")
        self.assertEqual(row["status"], "CONTRADICTED")

    def test_return_without_readback_is_not_a_verified_write(self):
        source = "before=0x41414141\nexpected=0xDEADBEEF\nsecond=0xCAFEBABE\n"
        log = "before=0x41414141\nRV=0x0 OK=true TID=7\n"
        temp, root = self.make_checkout(source, log)
        with temp:
            row = next(row for row in audit_external_probes(root)["probes"] if row["probe"] == "80i")
        self.assertEqual(row["status"], "CLAIMED BUT NOT DEMONSTRATED")
        self.assertFalse(row["completion_detected"])
        self.assertTrue(row["operation_return_detected"])

    def test_index_success_claim_is_reported_when_capture_is_incomplete(self):
        temp, root = self.make_checkout("expected=0xDEADBEEF second=0xCAFEBABE", "CALLING\n")
        with temp:
            report = audit_external_probes(root)
        row = next(row for row in report["probes"] if row["probe"] == "80i")
        self.assertEqual(row["claim_vs_evidence"], "CLAIM EXCEEDS SAVED EVIDENCE")
        self.assertTrue(report["claim_discrepancies"])
        rendered = render_probe_audit(report)
        self.assertIn("Index claims exceeding saved evidence", rendered)
        self.assertIn("SHA-256", rendered)

    def test_three_marker_capture_can_support_rop_without_final_banner(self):
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            (root / "probes").mkdir()
            (root / "results").mkdir()
            (root / "probes" / "80k_chain.lua").write_text(
                "0x41414141 0x42424242 0x43434343 0xDEADBEEF 0xCAFEBABE 0x12345678",
                encoding="utf-8")
            (root / "results" / "80k_capture.txt").write_text(
                "before: 41414141 42424242 43434343\n"
                "RV=0x0 OK=true TID=0x123 m0=DEADBEEF m4=CAFEBABE m8=12345678\n",
                encoding="utf-8")
            row = next(row for row in audit_external_probes(root)["probes"] if row["probe"] == "80k")
        self.assertEqual(row["status"], "VERIFIED FROM RAW EVIDENCE")
        self.assertFalse(row["completion_detected"])
        self.assertTrue(row["operation_return_detected"])


if __name__ == "__main__":
    unittest.main()
