"""Summarize official Sony OSS ZIPs without extracting or committing source."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile

ARCHIVES = {
    "WebKit_1400.zip": {
        "url": "https://www.playstation.com/content/dam/global_pdc/en-us/external-resources/oss/PS5/webkit/WebKit_1400.zip",
        "prefix": "WebKit-1400/WebKit-1400/",
    },
    "JSC-800.zip": {
        "url": "https://secure.cdn.us.playstation.com/oss/PS5/webkit-javascriptcore/JSC-800.zip",
        "prefix": "JSC-800/",
    },
}
TARGET = "Source/JavaScriptCore/dfg/DFGStoreBarrierInsertionPhase.cpp"


def inspect(path: Path, prefix: str) -> dict:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    with ZipFile(path) as archive:
        file_bytes = archive.read(prefix + TARGET)
        source = file_bytes.decode("utf-8", errors="replace")
        version_path = prefix + "Configurations/Version.xcconfig"
        version = None
        if version_path in archive.namelist():
            text = archive.read(version_path).decode("utf-8", errors="replace")
            parts = [re.search(rf"^{key}_VERSION = (\d+);", text, re.M) for key in ("MAJOR", "MINOR", "TINY", "MICRO", "NANO")]
            if all(parts):
                version = ".".join(match.group(1) for match in parts)
        changelog = prefix + "Source/JavaScriptCore/ChangeLog"
        first_changelog_line = archive.read(changelog).decode("utf-8", errors="replace").splitlines()[0] if changelog in archive.namelist() else None
        return {
            "bytes": path.stat().st_size,
            "sha256": digest.hexdigest(),
            "entries": len(archive.infolist()),
            "webkit_source_version": version,
            "jsc_changelog_first_line": first_changelog_line,
            "dfg_file_sha256": hashlib.sha256(file_bytes).hexdigest(),
            "dfg_has_transitive_incoming_call": "forAllTransitiveIncomingValues" in source,
            "dfg_has_direct_escape_epoch": "node->setEpoch(Epoch())" in source,
            "dfg_has_potential_stack_escape_direct_epoch": bool(re.search(r"potentialStackEscapes\.removeIf[\s\S]{0,250}entry\.value->setEpoch\(Epoch\(\)\)", source)),
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-dir", type=Path, default=Path("artifacts/sony-oss"))
    parser.add_argument("--output", type=Path, default=Path("notes/source-archive-analysis-2026-10-20.json"))
    args = parser.parse_args()
    report = {"scope": "Official Sony OSS source ZIPs; no firmware or console tested", "archives": {}}
    for name, metadata in ARCHIVES.items():
        report["archives"][name] = {"url": metadata["url"], **inspect(args.archive_dir / name, metadata["prefix"])}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
