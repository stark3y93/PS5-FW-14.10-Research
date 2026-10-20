"""Synthetic-only tests for bounded wrapper boundary measurements."""

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ps5fwlab.neighborhood import map_neighborhood, profile_bytes
from test_slb2 import package


class NeighborhoodTests(unittest.TestCase):
    def map(self, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.pup"
            path.write_bytes(data)
            return map_neighborhood(path, hashlib.sha256(data).hexdigest())

    def test_partitions_entire_file_without_overlap(self):
        result = self.map(package())
        self.assertEqual(result["slb2"]["version"], 3)
        self.assertEqual(result["slb2"]["block_count"], 3)
        self.assertEqual(result["slb2"]["entries"],
                         [{"name": "PS5UPDATE1.PUP", "block_offset": 2,
                           "offset": 1024, "size": 100,
                           "unknown_1": 0, "unknown_2": 0}])
        regions = result["regions"]
        self.assertEqual([r["kind"] for r in regions],
                         ["header", "entry_table", "header_unused", "gap", "entry", "gap"])
        self.assertEqual([(r["start"], r["end"]) for r in regions],
                         [(0, 32), (32, 80), (80, 512), (512, 1024),
                          (1024, 1124), (1124, 1536)])
        self.assertEqual(sum(r["size"] for r in regions), 1536)

    def test_multiple_entries_and_exact_eof(self):
        data = package(total_blocks=4, entries=((1, 100, b"A.PUP"),
                                                (3, 512, b"B.PUP")))
        result = self.map(data)
        self.assertEqual([(r["kind"], r["size"]) for r in result["regions"]],
                         [("header", 32), ("entry_table", 96),
                          ("header_unused", 384), ("entry", 100),
                          ("gap", 924), ("entry", 512)])

    def test_rejects_hash_mismatch_before_mapping(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.pup"
            path.write_bytes(package())
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                map_neighborhood(path, "0" * 64)

    def test_rejects_file_changed_during_mapping(self):
        data = package()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.pup"
            path.write_bytes(data)
            digest = hashlib.sha256(data).hexdigest()
            original_profile = profile_bytes

            def mutate_after_profile(sample):
                result = original_profile(sample)
                with path.open("r+b") as source:
                    source.seek(-1, 2)
                    source.write(b"X")
                return result

            with patch("ps5fwlab.neighborhood.profile_bytes", side_effect=mutate_after_profile):
                with self.assertRaisesRegex(ValueError, "changed during boundary mapping"):
                    map_neighborhood(path, digest)

    def test_nonzero_gap_edges_and_source_preservation(self):
        data = package(total_blocks=4, entries=((2, 513, b"A.PUP"),))
        data[512:544] = b"X" * 32
        data[992:1024] = b"Y" * 32
        original = bytes(data)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.pup"
            path.write_bytes(original)
            result = map_neighborhood(path, hashlib.sha256(original).hexdigest())
            self.assertEqual(path.read_bytes(), original)
        gap = next(r for r in result["regions"] if r["kind"] == "gap" and r["start"] == 512)
        self.assertEqual(gap["samples"][0]["nonzero_runs"], [[0, 32], [480, 512]])
        entry = next(r for r in result["regions"] if r["kind"] == "entry")
        self.assertEqual([(s["start"], s["end"]) for s in entry["samples"]],
                         [(1024, 1536), (1536, 1537)])

    def test_profiles_counts_entropy_and_nonzero_runs(self):
        result = profile_bytes(b"\0\x01\x01\0\x02\0")
        self.assertEqual(result["byte_frequencies"][0], 3)
        self.assertEqual(result["byte_frequencies"][1], 2)
        self.assertEqual(result["distinct_bytes"], 3)
        self.assertEqual(result["nonzero_runs"], [[1, 3], [4, 5]])
        self.assertGreater(result["entropy_bits_per_byte"], 0)

    def test_rejects_malformed_container_and_invalid_digest(self):
        with self.assertRaises(ValueError):
            self.map(b"SLB2")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.pup"
            path.write_bytes(package())
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                map_neighborhood(path, "bad")


if __name__ == "__main__":
    unittest.main()
