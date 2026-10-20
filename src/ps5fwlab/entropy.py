"""Deterministic, bounded byte statistics over a selected file interval."""

from __future__ import annotations

import math
import os
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


MAX_WINDOW_SIZE = 8 * 1024 * 1024
MAX_SAMPLES = 1024


@dataclass(frozen=True)
class EntropySample:
    offset: int
    length: int
    entropy_bits_per_byte: float
    zero_fraction: float
    printable_ascii_fraction: float


def sample_entropy(
    path: str | Path, *, offset: int, size: int, window_size: int = 65536, samples: int = 32
) -> tuple[EntropySample, ...]:
    """Sample evenly spaced windows without reading outside the selected range."""

    with Path(path).open("rb") as source:
        file_size = os.fstat(source.fileno()).st_size
        if offset < 0 or size <= 0 or offset > file_size or size > file_size - offset:
            raise ValueError("sample range lies outside the file")
        if not 1 <= window_size <= min(size, MAX_WINDOW_SIZE):
            raise ValueError("window size is invalid for this range")
        if not 1 <= samples <= MAX_SAMPLES:
            raise ValueError("sample count is outside the supported range")

        span = size - window_size
        positions = [offset] if samples == 1 else [offset + span * index // (samples - 1) for index in range(samples)]
        result: list[EntropySample] = []
        for position in dict.fromkeys(positions):
            source.seek(position)
            data = source.read(window_size)
            if len(data) != window_size:
                raise OSError("short read during entropy sample")
            counts = Counter(data)
            entropy = -sum((count / window_size) * math.log2(count / window_size) for count in counts.values())
            result.append(
                EntropySample(
                    offset=position,
                    length=window_size,
                    entropy_bits_per_byte=entropy,
                    zero_fraction=counts.get(0, 0) / window_size,
                    printable_ascii_fraction=sum(count for byte, count in counts.items() if 32 <= byte <= 126) / window_size,
                )
            )
    return tuple(result)
