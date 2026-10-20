"""Tests for bounded, deterministic entropy samples."""

import tempfile
import unittest
from pathlib import Path

from ps5fwlab.entropy import sample_entropy


class EntropyTests(unittest.TestCase):
    def sample(self, data, **kwargs):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.bin"
            path.write_bytes(data)
            before = path.read_bytes()
            result = sample_entropy(path, **kwargs)
            self.assertEqual(path.read_bytes(), before)
            return result

    def test_zero_window_has_zero_entropy(self):
        result = self.sample(bytes(64), offset=0, size=64, window_size=64, samples=1)
        self.assertEqual(result[0].entropy_bits_per_byte, 0.0)
        self.assertEqual(result[0].zero_fraction, 1.0)

    def test_uniform_byte_values_have_eight_bit_entropy(self):
        result = self.sample(bytes(range(256)), offset=0, size=256, window_size=256, samples=1)
        self.assertAlmostEqual(result[0].entropy_bits_per_byte, 8.0)

    def test_samples_stay_inside_selected_range(self):
        data = b"X" * 10 + b"\x00" * 20 + bytes(range(1, 21)) + b"Y" * 10
        result = self.sample(data, offset=10, size=40, window_size=20, samples=3)
        self.assertEqual([item.offset for item in result], [10, 20, 30])
        self.assertEqual([item.zero_fraction for item in result], [1.0, 0.5, 0.0])

    def test_rejects_out_of_bounds_range(self):
        with self.assertRaises(ValueError):
            self.sample(b"abc", offset=2, size=2, window_size=1, samples=1)

    def test_rejects_window_larger_than_range(self):
        with self.assertRaises(ValueError):
            self.sample(b"abc", offset=0, size=3, window_size=4, samples=1)


if __name__ == "__main__":
    unittest.main()
