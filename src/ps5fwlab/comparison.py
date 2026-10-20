"""Compare hash-verified SLB2 maps without reading payload interiors."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence
import math

from .neighborhood import map_neighborhood


def _complete_profile(region: dict | None) -> dict | None:
    """Combine adjacent edge profiles only when they cover the whole region."""

    if region is None:
        return None
    samples = region["samples"]
    if (not samples or samples[0]["start"] != region["start"]
            or samples[-1]["end"] != region["end"]
            or any(left["end"] != right["start"]
                   for left, right in zip(samples, samples[1:]))):
        return None
    frequencies = [sum(sample["byte_frequencies"][byte] for sample in samples)
                   for byte in range(256)]
    length = region["size"]
    runs: list[list[int]] = []
    for sample in samples:
        for start, end in sample["nonzero_runs"]:
            absolute_start = sample["start"] + start
            absolute_end = sample["start"] + end
            if runs and runs[-1][1] == absolute_start:
                runs[-1][1] = absolute_end
            else:
                runs.append([absolute_start, absolute_end])
    return {
        "zero_bytes": frequencies[0],
        "distinct_bytes": sum(bool(count) for count in frequencies),
        "entropy_bits_per_byte": -sum((count / length) * math.log2(count / length)
                                     for count in frequencies if count),
        "nonzero_runs": runs,
    }


def _sample_summary(sample_id: str, mapped: dict) -> dict:
    metadata = mapped["slb2"]
    entries = metadata["entries"]
    first_start = min(entry["offset"] for entry in entries)
    gap = next((region for region in mapped["regions"]
                if region["kind"] == "gap" and region["start"] == 512
                and region["end"] == first_start), None)
    gap_profile = _complete_profile(gap)
    final = mapped["regions"][-1]
    final_gap = final if final["kind"] == "gap" and final["end"] == mapped["file_size"] else None
    final_profile = _complete_profile(final_gap)
    header_regions = [region for region in mapped["regions"]
                      if region["kind"] in {"header", "entry_table", "header_unused"}]
    return {
        "sample_id": sample_id,
        "sha256": mapped["sha256"],
        "file_size": mapped["file_size"],
        "slb2_version": metadata["version"],
        "block_count": metadata["block_count"],
        "header_unknowns": [metadata[f"unknown_{number}"] for number in range(1, 5)],
        "header_region_sizes": [region["size"] for region in header_regions],
        "header_region_zero_bytes": [region["samples"][0]["zero_bytes"]
                                     for region in header_regions],
        "entry_records": entries,
        "entry_start_blocks": [entry["block_offset"] for entry in entries],
        "entry_sizes": [entry["size"] for entry in entries],
        "entry_end_mod_512": [(entry["offset"] + entry["size"]) % 512
                              for entry in entries],
        "pre_entry_interval": [gap["start"], gap["end"]] if gap else None,
        "pre_entry_runs": gap_profile["nonzero_runs"] if gap_profile else None,
        "pre_entry_fully_measured": gap_profile is not None,
        "pre_entry_zero_bytes": gap_profile["zero_bytes"] if gap_profile else None,
        "pre_entry_distinct_bytes": gap_profile["distinct_bytes"] if gap_profile else None,
        "pre_entry_entropy_bits_per_byte": gap_profile["entropy_bits_per_byte"] if gap_profile else None,
        "final_padding_size": final_gap["size"] if final_gap else 0,
        "final_padding_zero_bytes": (
            final_profile["zero_bytes"] if final_profile else None
        ),
        "final_padding_all_zero": (
            final_profile["zero_bytes"] == final_gap["size"]
            if final_profile else None
        ),
    }


def compare_packages(packages: Sequence[tuple[str, str | Path, str, int]]) -> dict:
    """Compare at least two distinct local packages identified by expected hashes.

    Sample IDs are caller-provided labels, not authenticated firmware versions.
    Package version/provenance must be established independently from official
    Sony evidence before interpreting a result as a cross-version comparison.
    """

    if len(packages) < 2:
        raise ValueError("comparison requires at least two packages")
    ids = [sample_id for sample_id, _, _, _ in packages]
    if len(set(ids)) != len(ids) or any(not sample_id for sample_id in ids):
        raise ValueError("sample IDs must be distinct and nonempty")
    expected = [digest.lower() for _, _, digest, _ in packages]
    if len(set(expected)) != len(expected):
        raise ValueError("package SHA-256 values must be distinct")

    samples = []
    for sample_id, path, digest, expected_size in packages:
        if expected_size <= 0 or Path(path).stat().st_size != expected_size:
            raise ValueError("package does not match expected size")
        mapped = map_neighborhood(path, digest)
        if mapped["file_size"] != expected_size:
            raise ValueError("package size changed during comparison")
        samples.append(_sample_summary(sample_id, mapped))

    def relationship(field: str) -> str:
        values = [sample[field] for sample in samples]
        return "same" if all(value == values[0] for value in values[1:]) else "different"

    patterns = []
    for sample in samples:
        interval = sample["pre_entry_interval"]
        runs = sample["pre_entry_runs"]
        if interval is None or runs is None:
            pattern = None
        else:
            pattern = (interval[1] - interval[0],
                       tuple((start - interval[0], end - interval[0])
                             for start, end in runs))
        patterns.append(pattern)
    pattern_relationship = (
        "inconclusive" if any(pattern is None for pattern in patterns) else
        "same" if all(pattern == patterns[0] for pattern in patterns[1:]) else
        "different"
    )
    return {
        "method": "hash-verified bounded SLB2 metadata; sample IDs are unverified labels",
        "samples": samples,
        "file_sizes": relationship("file_size"),
        "slb2_versions": relationship("slb2_version"),
        "header_unknowns": relationship("header_unknowns"),
        "header_region_sizes": relationship("header_region_sizes"),
        "header_region_zero_bytes": relationship("header_region_zero_bytes"),
        "entry_start_blocks": relationship("entry_start_blocks"),
        "entry_sizes": relationship("entry_sizes"),
        "entry_end_alignment": relationship("entry_end_mod_512"),
        "pre_entry_pattern": pattern_relationship,
        "final_padding_sizes": relationship("final_padding_size"),
    }
