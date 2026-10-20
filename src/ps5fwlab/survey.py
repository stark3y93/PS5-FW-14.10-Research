"""Predeclared, PC-only selection of disjoint firmware byte windows."""

from __future__ import annotations

import hashlib
import random
import re
from pathlib import Path

from .entropy import MAX_SAMPLES, MAX_WINDOW_SIZE

MAX_SURVEY_SLOTS = 1_000_000


def sha256_file(path: str | Path) -> str:
    """Hash a local file in bounded chunks without retaining its contents."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def plan_survey_offsets(
    *, offset: int, size: int, window_size: int, samples: int,
    seed_sha256: str, prior_samples: int = 256,
) -> tuple[int, ...]:
    """Choose seeded, nonoverlapping aligned windows outside prior even samples.

    The sampling frame is the complete windows aligned to ``offset``. Windows
    overlapping the earlier evenly spaced design are excluded before sampling.
    """

    if not re.fullmatch(r"[0-9a-fA-F]{64}", seed_sha256):
        raise ValueError("seed must be a 64-character SHA-256 hex digest")
    if not 1 <= samples <= MAX_SAMPLES:
        raise ValueError("sample count is outside the supported range")
    candidates = _candidate_slots(offset, size, window_size, prior_samples)
    if samples > len(candidates):
        raise ValueError("not enough windows remain outside the prior survey")

    generator = random.Random(int(seed_sha256, 16))
    return tuple(offset + index * window_size for index in sorted(generator.sample(candidates, samples)))


def survey_frame_size(*, offset: int, size: int, window_size: int, prior_samples: int = 256) -> int:
    """Count eligible aligned windows after excluding earlier sampled regions."""

    return len(_candidate_slots(offset, size, window_size, prior_samples))


def _candidate_slots(offset: int, size: int, window_size: int, prior_samples: int) -> list[int]:
    if offset < 0 or size <= 0 or not 1 <= window_size <= min(size, MAX_WINDOW_SIZE):
        raise ValueError("invalid survey interval or window size")
    if not 1 <= prior_samples <= MAX_SAMPLES:
        raise ValueError("sample count is outside the supported range")

    slot_count = size // window_size
    if slot_count > MAX_SURVEY_SLOTS:
        raise ValueError("survey slot frame exceeds the supported limit")
    span = size - window_size
    if prior_samples > span + 1:
        raise ValueError("prior survey has more samples than distinct window starts")
    prior_positions = (
        [offset] if prior_samples == 1 else
        [offset + span * index // (prior_samples - 1) for index in range(prior_samples)]
    )
    blocked: set[int] = set()
    for previous in prior_positions:
        slot, remainder = divmod(previous - offset, window_size)
        blocked.add(slot)
        if remainder:
            blocked.add(slot + 1)
    return [index for index in range(slot_count) if index not in blocked]


def zero_hit_upper_bound(samples: int, confidence: float = 0.95) -> float:
    """Conservative one-sided binomial upper bound after zero threshold hits."""

    if samples <= 0 or not 0 < confidence < 1:
        raise ValueError("invalid sample count or confidence")
    return 1 - (1 - confidence) ** (1 / samples)
