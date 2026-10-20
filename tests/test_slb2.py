"""Behavior tests for read-only SLB2 metadata inspection."""

import struct
import tempfile
import unittest
from random import Random
from pathlib import Path

from ps5fwlab.slb2 import SLB2Error, parse_slb2


def package(*, total_blocks=3, entries=((2, 100, b"PS5UPDATE1.PUP"),)):
    data = bytearray(total_blocks * 512)
    struct.pack_into("<4s7I", data, 0, b"SLB2", 3, 0, len(entries), total_blocks, 0, 0, 0)
    for index, (block, size, name) in enumerate(entries):
        struct.pack_into("<4I32s", data, 0x20 + index * 0x30, block, size, 0, 0, name)
    return data


class SLB2Tests(unittest.TestCase):
    def parse(self, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.pup"
            path.write_bytes(data)
            return parse_slb2(path)

    def test_reads_entry_offset_and_size_without_extraction(self):
        result = self.parse(package())
        self.assertEqual(result.version, 3)
        self.assertEqual(result.file_size, 1536)
        self.assertEqual(len(result.entries), 1)
        self.assertEqual(result.entries[0].name, "PS5UPDATE1.PUP")
        self.assertEqual((result.entries[0].offset, result.entries[0].size), (1024, 100))

    def test_rejects_wrong_magic(self):
        data = package()
        data[:4] = b"NOPE"
        with self.assertRaises(SLB2Error):
            self.parse(data)

    def test_rejects_truncated_header(self):
        with self.assertRaises(SLB2Error):
            self.parse(b"SLB2")

    def test_rejects_declared_length_mismatch(self):
        data = package()
        struct.pack_into("<I", data, 0x10, 4)
        with self.assertRaises(SLB2Error):
            self.parse(data)

    def test_rejects_entry_count_over_header_capacity(self):
        data = package()
        struct.pack_into("<I", data, 0x0C, 11)
        with self.assertRaises(SLB2Error):
            self.parse(data)

    def test_rejects_zero_entry_count(self):
        data = package()
        struct.pack_into("<I", data, 0x0C, 0)
        with self.assertRaises(SLB2Error):
            self.parse(data)

    def test_rejects_entry_inside_header(self):
        with self.assertRaises(SLB2Error):
            self.parse(package(entries=((0, 100, b"PART.PUP"),)))

    def test_rejects_entry_past_end(self):
        with self.assertRaises(SLB2Error):
            self.parse(package(entries=((2, 513, b"PART.PUP"),)))

    def test_rejects_overlapping_entries(self):
        with self.assertRaises(SLB2Error):
            self.parse(package(entries=((1, 600, b"ONE.PUP"), (2, 100, b"TWO.PUP"))))

    def test_rejects_unsafe_name(self):
        with self.assertRaises(SLB2Error):
            self.parse(package(entries=((2, 100, b"../PART.PUP"),)))

    def test_rejects_non_ascii_name(self):
        with self.assertRaises(SLB2Error):
            self.parse(package(entries=((2, 100, b"PART\xff.PUP"),)))

    def test_rejects_nonzero_name_padding(self):
        with self.assertRaises(SLB2Error):
            self.parse(package(entries=((2, 100, b"PART.PUP\x00X"),)))

    def test_rejects_zero_length_entry(self):
        with self.assertRaises(SLB2Error):
            self.parse(package(entries=((2, 0, b"PART.PUP"),)))

    def test_rejects_duplicate_entry_names(self):
        with self.assertRaises(SLB2Error):
            self.parse(package(total_blocks=4, entries=((2, 100, b"PART.PUP"), (3, 100, b"PART.PUP"))))

    def test_accepts_entry_ending_at_file_boundary(self):
        result = self.parse(package(entries=((2, 512, b"PART.PUP"),)))
        self.assertEqual(result.entries[0].offset + result.entries[0].size, result.file_size)

    def test_rejects_uint32_maximum_offset_and_block_count(self):
        data = package()
        struct.pack_into("<I", data, 0x20, 0xFFFFFFFF)
        with self.assertRaises(SLB2Error):
            self.parse(data)
        data = package()
        struct.pack_into("<I", data, 0x10, 0xFFFFFFFF)
        with self.assertRaises(SLB2Error):
            self.parse(data)

    def test_rejects_every_truncated_header_length(self):
        data = package()
        for length in range(512):
            with self.subTest(length=length), self.assertRaises(SLB2Error):
                self.parse(data[:length])

    def test_deterministic_header_mutations_never_escape_bounded_metadata(self):
        random = Random(1410)
        header_fields = (0, 0x0C, 0x10, 0x20, 0x24, 0x30)
        for trial in range(128):
            data = package()
            position = random.choice(header_fields) + random.randrange(4)
            data[position] ^= 1 << random.randrange(8)
            with self.subTest(trial=trial, position=position):
                try:
                    result = self.parse(data)
                except SLB2Error:
                    continue
                for entry in result.entries:
                    self.assertGreaterEqual(entry.offset, 512)
                    self.assertGreater(entry.size, 0)
                    self.assertLessEqual(entry.offset + entry.size, result.file_size)


if __name__ == "__main__":
    unittest.main()
