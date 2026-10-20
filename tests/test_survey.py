"""Synthetic tests for a hash-seeded, disjoint-window survey."""

import tempfile
import unittest
from pathlib import Path

from ps5fwlab.entropy import sample_entropy_at_offsets
from ps5fwlab.survey import plan_survey_offsets, survey_frame_size, zero_hit_upper_bound


class SurveyTests(unittest.TestCase):
    def test_plan_is_repeatable_disjoint_and_avoids_prior_windows(self):
        kwargs = dict(offset=512, size=4096, window_size=256, samples=4,
                      seed_sha256="0" * 64, prior_samples=3)
        first = plan_survey_offsets(**kwargs)
        self.assertEqual(first, plan_survey_offsets(**kwargs))
        self.assertEqual(len(first), 4)
        self.assertEqual(len(set(first)), 4)
        self.assertEqual(first, tuple(sorted(first)))
        prior = (512, 2432, 4352)
        for start in first:
            self.assertGreaterEqual(start, 512)
            self.assertLessEqual(start + 256, 4608)
            self.assertEqual((start - 512) % 256, 0)
            for old in prior:
                self.assertTrue(start + 256 <= old or old + 256 <= start)

    def test_plan_rejects_insufficient_unsampled_slots(self):
        with self.assertRaises(ValueError):
            plan_survey_offsets(offset=0, size=1024, window_size=256,
                                samples=3, seed_sha256="0" * 64, prior_samples=2)

    def test_frame_size_counts_only_unsampled_aligned_slots(self):
        self.assertEqual(survey_frame_size(offset=512, size=4096,
                                           window_size=256, prior_samples=3), 12)

    def test_plan_rejects_invalid_digest(self):
        with self.assertRaises(ValueError):
            plan_survey_offsets(offset=0, size=4096, window_size=256,
                                samples=1, seed_sha256="not-a-digest", prior_samples=2)

    def test_plan_rejects_excessive_slot_frame_without_allocating_it(self):
        with self.assertRaisesRegex(ValueError, "slot frame"):
            plan_survey_offsets(offset=0, size=1_000_003, window_size=1,
                                samples=1, seed_sha256="0" * 64, prior_samples=2)

    def test_explicit_offsets_are_bounded_and_read_only(self):
        data = bytes(range(256)) + bytes(256) + bytes(range(256))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.bin"
            path.write_bytes(data)
            result = sample_entropy_at_offsets(path, offset=0, size=len(data),
                                               window_size=256, positions=(0, 256))
            self.assertEqual([sample.offset for sample in result], [0, 256])
            self.assertEqual(result[0].entropy_bits_per_byte, 8.0)
            self.assertEqual(result[1].entropy_bits_per_byte, 0.0)
            self.assertEqual(path.read_bytes(), data)
            with self.assertRaises(ValueError):
                sample_entropy_at_offsets(path, offset=0, size=len(data),
                                          window_size=256, positions=(600,))

    def test_zero_hit_upper_bound(self):
        self.assertAlmostEqual(zero_hit_upper_bound(256), 1 - 0.05 ** (1 / 256))
        with self.assertRaises(ValueError):
            zero_hit_upper_bound(0)


if __name__ == "__main__":
    unittest.main()
