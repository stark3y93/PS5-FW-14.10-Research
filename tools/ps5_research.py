#!/usr/bin/env python3
"""Read-only, offline evidence audit for the PS5 14.10 research checkout.

This tool reports observations and contradictions; a pattern hit is never proof of
a vulnerability or of the code's presence in a retail firmware image.
"""

import argparse
import hashlib
import json
import re
import sys
import difflib
from dataclasses import asdict
from collections import Counter, defaultdict
from pathlib import Path


TEXT_EXTENSIONS = {".md", ".txt", ".json", ".py", ".js", ".html", ".c", ".s", ".sh"}
CODE_EXTENSIONS = {".py", ".js", ".html", ".c", ".s", ".sh"}
PATTERNS = {
    "iterator override": re.compile(r"Array\.prototype\s*\[\s*Symbol\.iterator\s*\]"),
    "large allocation": re.compile(r"(?:ArrayBuffer|Blob)\s*\("),
    "network operation": re.compile(r"(?:XMLHttpRequest|fetch\s*\(|socket\.)"),
    "native interface reference": re.compile(r"(?:syscall|ioctl)\s*\("),
}
CLAIM_TERMS = re.compile(r"CVE-\d{4}-\d{4,}|CSSFontFace|MetadataTable|Relapse|kernel exploit|corrupt(?:ed|ion)?", re.I)
CVES = re.compile(r"CVE-\d{4}-\d{4,}", re.I)


def files(root):
    """Yield relevant files without traversing Git internals or caches."""
    for path in sorted(root.rglob("*")):
        if path.is_file() and not any(p in {".git", "__pycache__", ".worktrees"} for p in path.parts):
            yield path


def location(root, path, line, excerpt):
    return {"file": path.relative_to(root).as_posix(), "line": line, "excerpt": excerpt.strip()[:240]}


def read_lines(path):
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def inventory(root):
    entries = []
    for path in files(root):
        entries.append({"file": path.relative_to(root).as_posix(), "bytes": path.stat().st_size,
                        "type": path.suffix.lower() or "(none)"})
    return entries


def parse_logs(root):
    events = []
    result_dir = root / "results"
    if not result_dir.exists():
        return events
    for path in files(result_dir):
        if path.suffix.lower() not in {".txt", ".log", ".jsonl"}:
            continue
        for number, raw in enumerate(read_lines(path), 1):
            tag, body = None, ""
            try:
                data = json.loads(raw)
                if isinstance(data, dict) and "path" in data:
                    tag = str(data["path"]).split("/beacon/")[-1]
                    body = str(data.get("body", ""))
            except json.JSONDecodeError:
                match = re.match(r"([A-Za-z0-9_-]+)(?:&|$)", raw)
                if match:
                    tag = match.group(1)
                    body = raw[match.end():]
            if tag:
                events.append({"tag": tag, "body": body, **location(root, path, number, raw)})
    return events


def evaluate_events(events):
    grouped = defaultdict(list)
    for event in events:
        match = re.match(r"(V\d+[A-Z]?|p\d+[A-Z]?)", event["tag"], re.I)
        if match:
            grouped[(event["file"], match.group(1).upper())].append(event)
    findings = []
    for (name, run), group in sorted(grouped.items()):
        tags = {e["tag"].upper() for e in group}
        negative = any("NO-CORRUPTION" in t for t in tags) and any(
            "HITS" in e["tag"].upper() and re.search(r"\b0-of-\d+\b", e["body"]) for e in group
        )
        started = any("CALLING" in t or "START" in t or "BOOT" in t for t in tags)
        ended = any(t == f"{run}-DONE" or t.startswith(f"{run}-SUMMARY")
                    or "NO-CORRUPTION" in t for t in tags)
        status = "negative-control" if negative else "incomplete" if started and not ended else "recorded"
        if status != "recorded":
            findings.append({"run": run, "status": status,
                             "evidence": [location_from_event(e) for e in group if
                                          "HITS" in e["tag"].upper() or "NO-CORRUPTION" in e["tag"].upper()
                                          or "CALLING" in e["tag"].upper() or "BOOT" in e["tag"].upper()]})
    return findings


def location_from_event(event):
    return {"file": event["file"], "line": event["line"],
            "excerpt": event.get("excerpt", event["tag"])}


def claim_lines(root):
    claims = []
    for path in files(root):
        if path.suffix.lower() not in {".md", ".json"}:
            continue
        for number, line in enumerate(read_lines(path), 1):
            if CLAIM_TERMS.search(line):
                claims.append({**location(root, path, number, line), "cves": sorted(set(CVES.findall(line)))})
    return claims


def detect_contradictions(root):
    old, new = [], []
    for claim in claim_lines(root):
        if claim["file"].startswith("analysis/false-positive") or claim["file"].startswith("reports/"):
            continue
        line = claim["excerpt"].lower()
        if ("81400" in line and "corrupt" in line
                and not any(word in line for word in ("false positive", "not corruption", "correction", "superseded", "unsupported", "disproved"))):
            old.append(claim)
        if "v480-no-corruption" in line or "0-of-14" in line:
            new.append(claim)
    log_new = []
    for event in parse_logs(root):
        if event["tag"] == "V480-post-compile-HITS" and re.search(r"\b0-of-\d+\b", event["body"]):
            log_new.append(location_from_event(event))
    if log_new:
        new = log_new
    if old and new:
        return [{"topic": "81400 string length described as corruption despite corrected V480 result",
                 "evidence": [old[0], new[0]]}]
    return []


def overflow_arithmetic(count=38_348_816, stride=112):
    """Synthetic 32-bit wrap calculation; does not model PS5 allocation or writes."""
    total = count * stride
    return {"count": count, "stride": stride, "mathematical_bytes": total,
            "uint32_bytes": total & 0xffffffff, "wrapped": total > 0xffffffff}


def checked_allocation_size(count, stride, maximum=0xffffffff):
    """Synthetic checked-size model; it does not allocate or model target code."""
    if count < 0 or stride < 0:
        raise ValueError("count and stride must be non-negative")
    total = count * stride
    if total > maximum:
        raise OverflowError("allocation size exceeds configured integer limit")
    return total


def index_in_bounds(index, length):
    """Model the safe 0 <= index < length predicate used in offline fixtures."""
    return 0 <= index < length


def compare_source_files(before, after):
    """Return a reproducible text diff summary for caller-supplied source snapshots."""
    before, after = Path(before), Path(after)
    left = read_lines(before)
    right = read_lines(after)
    diff = list(difflib.unified_diff(left, right, fromfile=before.name,
                                     tofile=after.name, lineterm=""))
    return {"before": before.name, "after": after.name,
            "before_sha256": hashlib.sha256(before.read_bytes()).hexdigest(),
            "after_sha256": hashlib.sha256(after.read_bytes()).hexdigest(),
            "removed_lines": [line[1:] for line in diff if line.startswith("-") and not line.startswith("---")],
            "added_lines": [line[1:] for line in diff if line.startswith("+") and not line.startswith("+++")],
            "unified_diff": "\n".join(diff)}


def scan_source(root):
    hits = []
    for path in files(root):
        if path.suffix.lower() not in CODE_EXTENSIONS:
            continue
        relative = path.relative_to(root)
        if "tests" in relative.parts or relative.as_posix() == "tools/ps5_research.py":
            continue
        for number, line in enumerate(read_lines(path), 1):
            for label, pattern in PATTERNS.items():
                if pattern.search(line):
                    hits.append({"pattern": label, **location(root, path, number, line)})
    return hits


def firmware_metadata(path, checksum=False):
    if path is None or not path.is_file():
        return {"present": False, "kernel_readable": False}
    with path.open("rb") as stream:
        header = stream.read(128)
        digest = None
        if checksum:
            stream.seek(0)
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
    result = {"present": True, "file": path.name, "bytes": path.stat().st_size,
            "container_magic": header[:4].decode("ascii", errors="replace"),
            "header_hex": header[:32].hex(),
            "visible_marker": "PS5UPDATE1.PUP" if b"PS5UPDATE1.PUP" in header else None,
            "sha256": digest, "kernel_readable": False,
            "limitation": "Container header only; no decryption or embedded kernel/source verification."}
    source_dir = Path(__file__).resolve().parents[1] / "src"
    if source_dir.is_dir():
        sys.path.insert(0, str(source_dir))
        from ps5fwlab.slb2 import SLB2Error, parse_slb2
        try:
            result["validated_slb2"] = asdict(parse_slb2(path))
        except SLB2Error as exc:
            result["slb2_validation_error"] = str(exc)
    return result


def analyze(root, firmware=None, checksum=False):
    events = parse_logs(root)
    claims = claim_lines(root)
    return {"root": root.resolve().name, "inventory": inventory(root), "events": events,
            "event_findings": evaluate_events(events), "claims": claims,
            "contradictions": detect_contradictions(root), "static_hits": scan_source(root),
            "firmware": firmware_metadata(firmware, checksum),
            "synthetic_metadata_arithmetic": overflow_arithmetic(),
            "limitations": ["Documentation is an assertion, not a firmware source dump.",
                            "A missing end beacon does not identify a crash cause.",
                            "Static pattern matches do not prove memory corruption or reachability."]}


def render(report, external=False):
    counts = Counter(item["type"] for item in report["inventory"])
    v480 = next((e for e in report["events"] if e["tag"] == "V480-post-compile-HITS"), None)
    css = next((e for e in report["claims"] if e["file"] == "docs/bugs/cssfontface-uaf.md"), None)
    metadata = next((e for e in report["claims"] if e["file"] == "docs/bugs/metadatatable-overflow.md"), None)
    kernel = next((e for e in report["claims"] if e["file"] == "docs/KERNEL_AUDIT.md"), None)
    def cite(item):
        return f"`{item['file']}:{item['line']}`" if item else "no local citation"
    root_label = "<evidence checkout>" if external else "<repository root>"
    lines = ["# Offline PS5 research evidence report", "", f"Root: `{root_label}`", "",
             f"Inventoried {len(report['inventory'])} files; parsed {len(report['events'])} log events; "
             f"indexed {len(report['claims'])} claim lines.", "",
             "## Inventory", "", ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())), "",
             "## Ranked evidence", "",
             (f"1. **Observed negative control — V480:** {cite(v480)} reports zero hits in the corrected run. This rebuts the 81,400-length corruption interpretation."
              if v480 else "1. **V480:** no browser beacon log is present in this root."),
             (f"2. **Upstream candidate — CSSFontFace:** local claim {cite(css)}; no confirming crash log or PS5 WebKit source in this checkout."
              if css else "2. **CSSFontFace:** no local claim or source in this root."),
             (f"3. **Unresolved — MetadataTable:** local claim {cite(metadata)}; synthetic 32-bit wrap is reproducible, while PS5 heap corruption is unestablished."
              if metadata else "3. **MetadataTable:** synthetic 32-bit wrap is reproducible; no target source in this root."),
             (f"4. **Unresolved — kernel CVEs:** local claim {cite(kernel)}; applicability to PS5 14.10 and sandbox reachability are unestablished."
              if kernel else "4. **Kernel CVEs:** no 14.10 kernel source or result in this root."), "",
             "## Contradictions", ""]
    for finding in report["contradictions"]:
        lines.append(f"- {finding['topic']}: " + "; ".join(
            f"`{e['file']}:{e['line']}` {e['excerpt']}" for e in finding["evidence"]))
    lines += ["", "## Nondefinitive log endings", ""]
    for finding in report["event_findings"]:
        if finding["status"] == "incomplete":
            lines.append(f"- {finding['run']}: " + ", ".join(f"`{e['file']}:{e['line']}`" for e in finding["evidence"]))
    lines += ["", "## Static code patterns", ""]
    for label in PATTERNS:
        examples = [h for h in report["static_hits"] if h["pattern"] == label]
        suffix = "; ".join(f"`{h['file']}:{h['line']}`" for h in examples[:3])
        lines.append(f"- {label}: {len(examples)} hits" + (f"; examples {suffix}" if suffix else ""))
    lines.append("These are source-text matches, not identified vulnerabilities.")
    lines += ["", "## Firmware", "", json.dumps(report["firmware"], indent=2), "",
              "## Synthetic arithmetic", "", json.dumps(report["synthetic_metadata_arithmetic"], indent=2), "",
              "## Method limits", ""] + [f"- {item}" for item in report["limitations"]]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--firmware", type=Path, help="optional local PUP; only metadata is read")
    parser.add_argument("--evidence-root", type=Path,
                        help="optional second checkout containing browser probes/logs")
    parser.add_argument("--sha256", action="store_true", help="hash the entire PUP")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path, help="write new report; refuses to overwrite")
    parser.add_argument("--compare", nargs=2, metavar=("BEFORE", "AFTER"),
                        help="compare two caller-supplied text source snapshots and report hashes/diff")
    args = parser.parse_args(argv)
    if not args.root.is_dir():
        parser.error("--root must be a directory")
    if args.evidence_root and not args.evidence_root.is_dir():
        parser.error("--evidence-root must be a directory")
    if args.compare:
        before, after = map(Path, args.compare)
        if not before.is_file() or not after.is_file():
            parser.error("--compare inputs must be existing files")
        payload = json.dumps(compare_source_files(before, after), indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(payload)
        else:
            print(payload, end="")
        return 0
    report = analyze(args.root, args.firmware, args.sha256)
    if args.evidence_root:
        report["external_evidence"] = analyze(args.evidence_root)
    payload = json.dumps(report, indent=2) + "\n" if args.format == "json" else render(report)
    if args.evidence_root and args.format == "markdown":
        payload += "\n## Separate browser evidence checkout\n\n" + render(report["external_evidence"], external=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(payload)
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
