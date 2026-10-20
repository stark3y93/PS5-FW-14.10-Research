import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SPEC = importlib.util.spec_from_file_location(
    "ps5_research", Path(__file__).resolve().parents[1] / "tools" / "ps5_research.py"
)
research = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(research)


class ResearchTests(unittest.TestCase):
    def test_parses_both_recorded_log_formats_with_locations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log = root / "results" / "run.txt"
            log.parent.mkdir()
            log.write_text(
                json.dumps({"path": "/beacon/V480-post-compile-HITS", "body": "0-of-14"})
                + "\nV150G-CALLING&t=123\n", encoding="utf-8"
            )
            events = research.parse_logs(root)
            self.assertEqual([(e["tag"], e["line"]) for e in events],
                             [("V480-post-compile-HITS", 1), ("V150G-CALLING", 2)])

    def test_false_positive_and_incomplete_run_are_distinct(self):
        events = [
            {"tag": "V480-post-compile-HITS", "body": "0-of-14", "file": "x", "line": 1},
            {"tag": "V480-NO-CORRUPTION", "body": "", "file": "x", "line": 2},
            {"tag": "V150G-CALLING", "body": "", "file": "x", "line": 3},
        ]
        findings = research.evaluate_events(events)
        self.assertTrue(any(f["status"] == "negative-control" for f in findings))
        self.assertTrue(any(f["status"] == "incomplete" for f in findings))

    def test_claim_conflict_cites_both_sides(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "old.md").write_text("All 14 strings corrupted, .length=81400\n")
            (root / "docs" / "new.md").write_text("V480-NO-CORRUPTION\n")
            conflicts = research.detect_contradictions(root)
            self.assertEqual(len(conflicts), 1)
            self.assertEqual(len(conflicts[0]["evidence"]), 2)

    def test_firmware_header_is_not_interpreted_as_decrypted_kernel(self):
        with tempfile.TemporaryDirectory() as tmp:
            pup = Path(tmp) / "PS5UPDATE.PUP"
            pup.write_bytes(b"SLB2" + bytes(44) + b"PS5UPDATE1.PUP" + bytes(64))
            metadata = research.firmware_metadata(pup)
            self.assertEqual(metadata["container_magic"], "SLB2")
            self.assertFalse(metadata["kernel_readable"])

    def test_static_hits_only_cite_real_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "p.js").write_text("Array.prototype[Symbol.iterator] = fn;\n")
            (root / "claim.md").write_text("Array.prototype[Symbol.iterator] = fn;\n")
            hits = research.scan_source(root)
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0]["file"], "p.js")

    def test_synthetic_overflow_wraps_without_claiming_device_write(self):
        value = research.overflow_arithmetic()
        self.assertEqual(value["mathematical_bytes"], 4_295_067_392)
        self.assertEqual(value["uint32_bytes"], 100_096)
        self.assertTrue(value["wrapped"])

    def test_distinct_lettered_runs_do_not_mask_incomplete_call(self):
        events = [
            {"tag": "V150G-CALLING", "body": "", "file": "log", "line": 1},
            {"tag": "V150G-GC-DONE", "body": "", "file": "log", "line": 2},
            {"tag": "V150L-DONE", "body": "", "file": "log", "line": 3},
        ]
        findings = research.evaluate_events(events)
        self.assertEqual([(f["run"], f["status"]) for f in findings],
                         [("V150G", "incomplete")])


if __name__ == "__main__":
    unittest.main()
