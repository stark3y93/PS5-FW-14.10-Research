"""Command-line entry point for offline, read-only package inspection."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .entropy import sample_entropy
from .slb2 import parse_slb2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ps5fwlab", description="Inspect SLB2 metadata without extracting payloads")
    commands = parser.add_subparsers(dest="command", required=True)
    inspect_command = commands.add_parser("inspect", help="validate and report the outer SLB2 table")
    inspect_command.add_argument("file", type=Path)
    entropy_command = commands.add_parser("entropy", help="sample byte statistics within validated entries")
    entropy_command.add_argument("file", type=Path)
    entropy_command.add_argument("--window", type=int, default=65536, help="bytes per sample (default: 65536)")
    entropy_command.add_argument("--samples", type=int, default=32, help="evenly spaced windows per entry (default: 32)")
    args = parser.parse_args(argv)

    metadata = parse_slb2(args.file)
    if args.command == "inspect":
        payload = asdict(metadata)
    else:
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
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
