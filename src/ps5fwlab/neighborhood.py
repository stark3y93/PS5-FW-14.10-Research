"""Hash-verified, bounded measurements around SLB2 wrapper boundaries.

All intervals are half-open. Large entry bodies are represented by at most
two 512-byte edge samples; this module does not characterize their interiors.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

from .slb2 import BLOCK_SIZE, ENTRY_SIZE, HEADER_SIZE, parse_slb2
from .survey import sha256_file


def profile_bytes(data: bytes) -> dict:
    """Return numeric byte statistics without exposing source bytes."""

    if not data:
        raise ValueError("cannot profile an empty interval")
    counts = [0] * 256
    for value in data:
        counts[value] += 1
    length = len(data)
    entropy = sum(-(count / length) * math.log2(count / length)
                  for count in counts if count)
    runs = []
    beginning = None
    for index, value in enumerate(data):
        if value and beginning is None:
            beginning = index
        elif not value and beginning is not None:
            runs.append([beginning, index])
            beginning = None
    if beginning is not None:
        runs.append([beginning, length])
    return {
        "byte_frequencies": counts,
        "zero_bytes": counts[0],
        "distinct_bytes": sum(bool(count) for count in counts),
        "entropy_bits_per_byte": entropy,
        "nonzero_runs": runs,
    }


def map_neighborhood(path: str | Path, expected_sha256: str) -> dict:
    """Partition a validated wrapper and measure only 512-byte edge samples."""

    if not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
        raise ValueError("expected SHA-256 must be 64 hexadecimal characters")
    path = Path(path)
    digest = sha256_file(path)
    if digest != expected_sha256.lower():
        raise ValueError("full-file SHA-256 does not match the expected value")
    metadata = parse_slb2(path)

    intervals: list[tuple[str, int, int, str | None]] = [
        ("header", 0, HEADER_SIZE, None),
        ("entry_table", HEADER_SIZE,
         HEADER_SIZE + len(metadata.entries) * ENTRY_SIZE, None),
        ("header_unused", HEADER_SIZE + len(metadata.entries) * ENTRY_SIZE,
         BLOCK_SIZE, None),
    ]
    cursor = BLOCK_SIZE
    for entry in sorted(metadata.entries, key=lambda item: item.offset):
        if cursor < entry.offset:
            intervals.append(("gap", cursor, entry.offset, None))
        intervals.append(("entry", entry.offset, entry.offset + entry.size,
                          entry.name))
        cursor = entry.offset + entry.size
    if cursor < metadata.file_size:
        intervals.append(("gap", cursor, metadata.file_size, None))

    regions = []
    with path.open("rb") as source:
        for kind, start, end, name in intervals:
            size = end - start
            if size <= 0:
                continue
            positions = [(start, end)] if size <= BLOCK_SIZE else [
                (start, start + BLOCK_SIZE),
                (start + BLOCK_SIZE if size <= 2 * BLOCK_SIZE else end - BLOCK_SIZE, end),
            ]
            samples = []
            for sample_start, sample_end in positions:
                source.seek(sample_start)
                data = source.read(sample_end - sample_start)
                if len(data) != sample_end - sample_start:
                    raise ValueError("short read while sampling wrapper boundary")
                samples.append({"start": sample_start, "end": sample_end,
                                **profile_bytes(data)})
            regions.append({
                "kind": kind, "name": name, "start": start, "end": end,
                "size": size, "start_mod_512": start % BLOCK_SIZE,
                "end_mod_512": end % BLOCK_SIZE, "samples": samples,
            })
    if sha256_file(path) != digest:
        raise ValueError("full-file SHA-256 changed during boundary mapping")
    return {
        "sha256": digest,
        "file_size": metadata.file_size,
        "method": "half-open regions; complete small regions or first and last 512 bytes only",
        "regions": regions,
    }
