"""Command-line entry point for offline, read-only package inspection."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from statistics import mean

from .comparison import compare_packages
from .entropy import sample_entropy, sample_entropy_at_offsets
from .neighborhood import map_neighborhood
from .slb2 import parse_slb2
from .survey import plan_survey_offsets, sha256_file, survey_frame_size, zero_hit_upper_bound


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ps5fwlab", description="Inspect SLB2 metadata without extracting payloads")
    commands = parser.add_subparsers(dest="command", required=True)
    inspect_command = commands.add_parser("inspect", help="validate and report the outer SLB2 table")
    inspect_command.add_argument("file", type=Path)
    entropy_command = commands.add_parser("entropy", help="sample byte statistics within validated entries")
    entropy_command.add_argument("file", type=Path)
    entropy_command.add_argument("--window", type=int, default=65536, help="bytes per sample (default: 65536)")
    entropy_command.add_argument("--samples", type=int, default=32, help="evenly spaced windows per entry (default: 32)")
    survey_command = commands.add_parser("survey", help="hash-verified independent byte-window survey")
    survey_command.add_argument("file", type=Path)
    survey_command.add_argument("--sha256", required=True, help="expected full-file SHA-256")
    survey_command.add_argument("--window", type=int, default=65536)
    survey_command.add_argument("--samples", type=int, default=256)
    survey_command.add_argument("--threshold", type=float, default=7.9)
    map_command = commands.add_parser("map", help="hash-verified SLB2 boundary statistics")
    map_command.add_argument("file", type=Path)
    map_command.add_argument("--sha256", required=True, help="expected full-file SHA-256")
    compare_command = commands.add_parser("compare", help="compare two or more hash-verified local wrappers")
    compare_command.add_argument("--package", nargs=4, action="append", required=True,
                                 metavar=("SAMPLE_ID", "FILE", "SHA256", "EXPECTED_SIZE"),
                                 help="repeat for each distinct package; sample IDs are not verified versions")
    args = parser.parse_args(argv)

    if args.command == "compare":
        packages = [(sample_id, path, digest, int(size))
                    for sample_id, path, digest, size in args.package]
        print(json.dumps(compare_packages(packages), indent=2))
        return 0

    if args.command == "map":
        print(json.dumps(map_neighborhood(args.file, args.sha256), indent=2))
        return 0

    metadata = parse_slb2(args.file)
    if args.command == "inspect":
        payload = asdict(metadata)
    elif args.command == "entropy":
        payload = {
            "file_size": metadata.file_size,
            "method": "evenly spaced byte windows; no decryption or executable analysis",
            "window_size": args.window,
            "requested_samples_per_entry": args.samples,
            "entries": [
                {
                    "name": entry.name,
                    "offset": entry.offset,
                    "size": entry.size,
                    "samples": [asdict(sample) for sample in sample_entropy(args.file, offset=entry.offset, size=entry.size, window_size=args.window, samples=args.samples)],
                }
                for entry in metadata.entries
            ],
        }
    else:
        if not 0 <= args.threshold <= 8:
            raise ValueError("entropy threshold must be between zero and eight")
        digest = sha256_file(args.file)
        if digest != args.sha256.lower():
            raise ValueError("full-file SHA-256 does not match the expected value")
        entries = []
        for entry in metadata.entries:
            positions = plan_survey_offsets(
                offset=entry.offset, size=entry.size, window_size=args.window,
                samples=args.samples, seed_sha256=digest, prior_samples=256,
            )
            measured = sample_entropy_at_offsets(
                args.file, offset=entry.offset, size=entry.size,
                window_size=args.window, positions=positions,
            )
            hits = sum(sample.entropy_bits_per_byte < args.threshold for sample in measured)
            entries.append({
                "name": entry.name,
                "offset": entry.offset,
                "size": entry.size,
                "aligned_full_window_slots": entry.size // args.window,
                "eligible_window_slots": survey_frame_size(
                    offset=entry.offset, size=entry.size, window_size=args.window,
                    prior_samples=256,
                ),
                "samples": [asdict(sample) for sample in measured],
                "below_threshold": hits,
                "min_entropy": min(sample.entropy_bits_per_byte for sample in measured),
                "mean_entropy": mean(sample.entropy_bits_per_byte for sample in measured),
                "max_entropy": max(sample.entropy_bits_per_byte for sample in measured),
                "uniform_slot_model_upper_fraction_95pct": zero_hit_upper_bound(len(measured)) if hits == 0 else None,
            })
        if sha256_file(args.file) != digest:
            raise ValueError("full-file SHA-256 changed during survey")
        payload = {
            "sha256": digest,
            "method": "SHA-256-seeded, aligned, disjoint windows excluding overlap with 256 prior evenly spaced windows",
            "window_size": args.window,
            "requested_samples_per_entry": args.samples,
            "threshold_bits_per_byte": args.threshold,
            "entries": entries,
        }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
