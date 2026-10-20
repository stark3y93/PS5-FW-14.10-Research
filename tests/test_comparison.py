"""Cross-container comparisons use synthetic data and verified hashes."""

import hashlib
import tempfile
import unittest
from pathlib import Path

from ps5fwlab.comparison import compare_packages
from test_slb2 import package


class ComparisonTests(unittest.TestCase):
    def write(self, root, name, data):
        path = root / name
        path.write_bytes(data)
        return (name, path, hashlib.sha256(data).hexdigest(), len(data))

    def test_equal_two_run_pattern_is_reported_stable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = package()
            second = package(total_blocks=4, entries=((2, 200, b"A.PUP"),))
            for data in (first, second):
                data[512:544] = b"A" * 32
                data[992:1024] = b"B" * 32
            result = compare_packages([self.write(root, "a", first),
                                       self.write(root, "b", second)])
            self.assertEqual(result["pre_entry_pattern"], "same")
            self.assertEqual(result["samples"][0]["pre_entry_runs"],
                             [[512, 544], [992, 1024]])
            self.assertEqual(result["samples"][1]["entry_sizes"], [200])
            self.assertEqual(result["entry_start_blocks"], "same")
            self.assertEqual(result["file_sizes"], "different")
            self.assertEqual(result["samples"][0]["pre_entry_zero_bytes"], 448)
            self.assertEqual(result["samples"][0]["final_padding_zero_bytes"], 412)
            self.assertEqual(result["header_region_sizes"], "same")
            self.assertEqual(result["samples"][0]["entry_end_mod_512"], [100])

    def test_changed_run_pattern_is_reported_different(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = package()
            second = package()
            first[512:544] = b"A" * 32
            second[512:528] = b"A" * 16
            result = compare_packages([self.write(root, "a", first),
                                       self.write(root, "b", second)])
            self.assertEqual(result["pre_entry_pattern"], "different")

    def test_unmeasured_middle_makes_run_comparison_inconclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            short = package()
            long = package(total_blocks=5, entries=((3, 100, b"A.PUP"),))
            result = compare_packages([self.write(root, "a", short),
                                       self.write(root, "b", long)])
            self.assertEqual(result["pre_entry_pattern"], "inconclusive")
            self.assertIsNone(result["samples"][1]["pre_entry_runs"])

    def test_rejects_duplicate_hash_and_invalid_container(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = self.write(root, "a", package())
            with self.assertRaisesRegex(ValueError, "distinct"):
                compare_packages([first, first])
            twin = self.write(root, "twin", package())
            with self.assertRaisesRegex(ValueError, "SHA-256 values must be distinct"):
                compare_packages([first, twin])
            bad = self.write(root, "bad", b"SLB2")
            with self.assertRaises(ValueError):
                compare_packages([first, bad])

    def test_rejects_fewer_than_two_and_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            first = self.write(Path(directory), "a", package())
            with self.assertRaisesRegex(ValueError, "two"):
                compare_packages([first])
            second = self.write(Path(directory), "b", package(total_blocks=4))
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                compare_packages([first, (second[0], second[1], "0" * 64, second[3])])
            with self.assertRaisesRegex(ValueError, "expected size"):
                compare_packages([first, (second[0], second[1], second[2], second[3] + 1)])

    def test_rejects_overlapping_entries_and_inconsistent_size(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            good = self.write(root, "good", package())
            overlapping = package(total_blocks=4,
                                  entries=((1, 600, b"A.PUP"), (2, 100, b"B.PUP")))
            bad_overlap = self.write(root, "overlap", overlapping)
            with self.assertRaisesRegex(ValueError, "overlap"):
                compare_packages([good, bad_overlap])
            wrong_size = package()
            wrong_size[16:20] = (4).to_bytes(4, "little")
            bad_size = self.write(root, "size", wrong_size)
            with self.assertRaisesRegex(ValueError, "block count"):
                compare_packages([good, bad_size])
            invalid_offset = package(total_blocks=4,
                                     entries=((4, 100, b"A.PUP"),))
            bad_offset = self.write(root, "offset", invalid_offset)
            with self.assertRaisesRegex(ValueError, "outside the file"):
                compare_packages([good, bad_offset])


if __name__ == "__main__":
    unittest.main()
