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
import subprocess
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


PROBE_IDS = tuple(f"80{letter}" for letter in "abcdefghijk")
WRITE_EXPECTATIONS = {
    "80c": (("DEADBEEF",), ("41414141",)),
    "80i": (("DEADBEEF", "CAFEBABE"), ("41414141",)),
    "80j": (("DEADBEEF",), ("41414141",)),
    "80k": (("DEADBEEF", "CAFEBABE", "12345678"),
            ("41414141", "42424242", "43434343")),
}
PROBE_TERMINAL = re.compile(r"(?:===\s*DONE\s*===|===\s*PROBE\s+80[a-k].*COMPLETE\s*===|\*\*\* ALL 3 WRITES CONFIRMED)", re.I)


def _completion_detected(probe_id, text):
    if PROBE_TERMINAL.search(text):
        return True
    # 80j emits its result in one combined line and has no separate terminal banner.
    return probe_id == "80j" and bool(re.search(
        r"RV=0x[0-9a-f]+\s+OK=(?:true|false)\s+M=0x[0-9a-f]{8}\s+TID=0x[0-9a-f_]+", text, re.I))


def _git_value(root, *args):
    try:
        return subprocess.run(["git", "-C", str(root), *args], check=True,
                              capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _git_blob_bytes(root, blob):
    try:
        return subprocess.run(["git", "-C", str(root), "cat-file", "blob", blob],
                              check=True, capture_output=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None


def _file_evidence(root, path, repo_url, revision):
    raw = path.read_bytes()
    rel = path.relative_to(root).as_posix()
    lines = read_lines(path)
    blob = _git_value(root, "rev-parse", f"HEAD:{rel}")
    blob_match = None
    canonical = _git_blob_bytes(root, blob) if blob else None
    if blob and len(blob) == 40:
        git_header = f"blob {len(raw)}\0".encode("ascii")
        blob_match = hashlib.sha1(git_header + raw).hexdigest() == blob
    normalized_match = None
    if canonical is not None:
        normalized_match = raw.replace(b"\r\n", b"\n") == canonical.replace(b"\r\n", b"\n")
    url = f"{repo_url.rstrip('/')}/blob/{revision}/{rel}" if repo_url and revision else None
    return {"path": rel, "line_count": len(lines),
            "sha256": hashlib.sha256(canonical if canonical is not None else raw).hexdigest(),
            "worktree_sha256": hashlib.sha256(raw).hexdigest(),
            "git_blob": blob, "worktree_matches_git_blob": blob_match,
            "text_matches_git_blob_after_newline_normalization": normalized_match, "url": url}


def _probe_status(probe_id, source_text, log_texts):
    all_logs = "\n".join(log_texts)
    complete = any(_completion_detected(probe_id, item) for item in log_texts)
    expected, baseline = WRITE_EXPECTATIONS.get(probe_id, ((), ()))
    if expected:
        source_has_values = all(re.search(rf"0x{value}", source_text, re.I) for value in expected)
        positive_run, explicit_mismatch, any_readback = False, False, False
        for log_text in log_texts:
            if probe_id == "80i":
                first = re.findall(r"MARKER\s*=\s*0x([0-9A-F]{8})(?![0-9A-F_])", log_text, re.I)
                second = re.findall(r"second write:\s*0x([0-9A-F]{8})", log_text, re.I)
                readbacks = first[-1:] + second[-1:]
            elif probe_id == "80c":
                readbacks = re.findall(r"marker after:\s*0x([0-9A-F]{8})", log_text, re.I)
            elif probe_id == "80j":
                readbacks = re.findall(r"M=0x([0-9A-F]{8})", log_text, re.I)
            else:
                readbacks = []
                for key in ("m0", "m4", "m8"):
                    found = re.findall(rf"{key}=([0-9A-F]{{8}})", log_text, re.I)
                    readbacks.append(found[-1] if found else "")
            explicit_mismatch |= any(value and value.upper() not in expected for value in readbacks)
            any_readback |= bool(readbacks)
            log_has_baseline = all(value in log_text.upper() for value in baseline)
            log_complete = _completion_detected(probe_id, log_text)
            operation_result = bool(re.search(r"RV=0x[0-9a-f]+", log_text, re.I))
            if source_has_values and log_has_baseline and tuple(v.upper() for v in readbacks) == expected and operation_result:
                positive_run = True
        if positive_run:
            return "VERIFIED FROM RAW EVIDENCE", complete
        if explicit_mismatch:
            return "CONTRADICTED", complete
        if complete or any_readback:
            return "PARTIALLY SUPPORTED", complete
        return "CLAIMED BUT NOT DEMONSTRATED", complete
    if not log_texts:
        return "INSUFFICIENT EVIDENCE", False
    if complete:
        return "PARTIALLY SUPPORTED", True
    return "CLAIMED BUT NOT DEMONSTRATED", False


def audit_external_probes(root, repo_url=None):
    """Cross-reference 80a-k sources and captures; hashes provide provenance, not authenticity."""
    root = Path(root).resolve()
    revision = _git_value(root, "rev-parse", "HEAD")
    repo_url = repo_url or _git_value(root, "remote", "get-url", "origin")
    if repo_url and repo_url.endswith(".git"):
        repo_url = repo_url[:-4]
    source_paths = sorted((root / "probes").rglob("80*.lua")) if (root / "probes").exists() else []
    log_paths = sorted(path for base in (root / "results",) if base.exists()
                       for path in base.rglob("80*") if path.is_file())
    claims_by_probe = defaultdict(list)
    index_path = root / "docs" / "PROBE_INDEX.md"
    if index_path.is_file():
        for number, line in enumerate(read_lines(index_path), 1):
            match = re.match(r"\|\s*(80[a-k])\s*\|.*", line, re.I)
            if match:
                cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
                claims_by_probe[match.group(1).lower()].append({
                    "file": index_path.relative_to(root).as_posix(), "line": number,
                    "excerpt": line.strip()[:320],
                    "index_status": cells[2] if len(cells) > 2 else "",
                    "claims_success": len(cells) > 2 and cells[2].upper() in {"OK", "PASS", "SUCCESS"}})
    rows = []
    for probe_id in PROBE_IDS:
        sources = [p for p in source_paths if re.match(rf"{probe_id}(?:[_\.]|$)", p.name, re.I)]
        logs = [p for p in log_paths if re.match(rf"{probe_id}(?:[_\.]|$)", p.name, re.I)]
        source_text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in sources)
        log_texts = [p.read_text(encoding="utf-8", errors="replace") for p in logs]
        status, complete = _probe_status(probe_id, source_text, log_texts)
        claims = claims_by_probe.get(probe_id, [])
        success_claimed = any(item["claims_success"] for item in claims)
        if not success_claimed:
            claim_vs_evidence = "NO SUCCESS CLAIM IN INDEX"
        elif status == "VERIFIED FROM RAW EVIDENCE":
            claim_vs_evidence = "SUPPORTED BY SAVED CAPTURE"
        elif status == "CONTRADICTED":
            claim_vs_evidence = "CONTRADICTED BY SAVED CAPTURE"
        else:
            claim_vs_evidence = "CLAIM EXCEEDS SAVED EVIDENCE"
        evidence = []
        for path in sources + logs:
            for number, line in enumerate(read_lines(path), 1):
                if re.search(r"(?:before:|before=|MARKER\s*=|RV=|m0=|CALLING|COMPLETE|DONE|thr_create)", line, re.I):
                    evidence.append({"path": path.relative_to(root).as_posix(), "line": number,
                                     "excerpt": line.strip()[:220]})
        captures = []
        for path, log_text in zip(logs, log_texts):
            capture_status, capture_complete = _probe_status(probe_id, source_text, [log_text])
            captures.append({"file": path.relative_to(root).as_posix(), "status": capture_status,
                             "completion_detected": capture_complete,
                             "operation_return_detected": bool(re.search(r"RV=0x[0-9a-f]+", log_text, re.I)),
                             "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        rows.append({"probe": probe_id, "status": status, "completion_detected": complete,
                     "operation_return_detected": bool(re.search(r"RV=0x[0-9a-f]+", "\n".join(log_texts), re.I)),
                     "claims": claims, "claim_vs_evidence": claim_vs_evidence,
                     "source_files": [_file_evidence(root, p, repo_url, revision) for p in sources],
                     "raw_logs": [_file_evidence(root, p, repo_url, revision) for p in logs],
                     "evidence_lines": evidence,
                     "capture_findings": captures,
                     "claim_source_match": bool(sources),
                     "limitations": ["Repository-authored logs are not independently authenticated.",
                                     "This audit does not execute probes or verify a console/firmware identity."]})
    contradictions = [{"probe": row["probe"], **capture} for row in rows
                      for capture in row["capture_findings"] if capture["status"] == "CONTRADICTED"]
    claim_discrepancies = [{"probe": row["probe"], "claim_vs_evidence": row["claim_vs_evidence"],
                            "claims": row["claims"], "status": row["status"]}
                           for row in rows if row["claim_vs_evidence"] == "CLAIM EXCEEDS SAVED EVIDENCE"]
    return {"repository": repo_url, "commit": revision, "probes": rows,
            "contradictions": contradictions, "claim_discrepancies": claim_discrepancies,
            "method": "Filename-linked source/log inventory, SHA-256 and Git blob provenance, terminal/readback pattern checks.",
            "timestamp_caveat": "Filename timestamps are labels; they are not independently authenticated capture times."}


def render_probe_audit(report):
    lines = ["# External thread execution evidence audit", "",
             f"Repository: {report.get('repository') or 'unknown'}",
             f"Commit: `{report.get('commit') or 'unavailable'}`", "",
             report["method"], "", report["timestamp_caveat"], "",
             "| Probe | Classification | Completion marker | Index claim | Sources | Raw captures |",
             "|---|---|---:|---|---:|---:|"]
    for row in report["probes"]:
        sources = ", ".join(f"[{item['path']}]({item['url']}) · SHA-256 `{item['sha256']}`" if item["url"] else f"`{item['path']}` · SHA-256 `{item['sha256']}`" for item in row["source_files"])
        logs = ", ".join(f"[{item['path']}]({item['url']}) · SHA-256 `{item['sha256']}`" if item["url"] else f"`{item['path']}` · SHA-256 `{item['sha256']}`" for item in row["raw_logs"])
        lines.append(f"| {row['probe']} | **{row['status']}** | {row['completion_detected']} | {row['claim_vs_evidence']} | {sources or 'none'} | {logs or 'none'} |")
    lines += ["", "## Evidence lines", ""]
    for row in report["probes"]:
        lines += [f"### {row['probe']} — {row['status']}", ""]
        if row["evidence_lines"]:
            lines.extend(f"- `{item['path']}:{item['line']}` `{item['excerpt']}`" for item in row["evidence_lines"])
        else:
            lines.append("- No source or raw log was found.")
    lines += ["", "## Contradictory captures", ""]
    if report["contradictions"]:
        lines.extend(f"- {item['probe']}: `{item['file']}` — {item['status']}" for item in report["contradictions"])
    else:
        lines.append("- No explicitly mismatched write readback detected.")
    lines += ["", "## Index claims exceeding saved evidence", ""]
    if report["claim_discrepancies"]:
        for item in report["claim_discrepancies"]:
            claims = "; ".join(f"`{claim['file']}:{claim['line']}` {claim['excerpt']}" for claim in item["claims"])
            lines.append(f"- {item['probe']}: {item['status']} — {claims}")
    else:
        lines.append("- None detected.")
    lines += ["", "## Interpretation limits", "",
              "A positive saved output supports that the repository records the expected userland operation. It does not authenticate the operator, console model, firmware version, capture integrity, or independent reproduction.",
              "An OS thread return code and marker readback do not demonstrate kernel execution, kernel read/write, a firmware vulnerability, or a jailbreak.",
              "Hashes identify the exact files audited; they do not prove when or where a file was created."]
    return "\n".join(lines) + "\n"


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
    parser.add_argument("--probe-audit", type=Path,
                        help="cross-reference public 80a-k Lua sources and saved captures")
    parser.add_argument("--probe-repo-url", help="canonical GitHub repository URL for evidence links")
    parser.add_argument("--sha256", action="store_true", help="hash the entire PUP")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path, help="write new report; refuses to overwrite")
    parser.add_argument("--compare", nargs=2, metavar=("BEFORE", "AFTER"),
                        help="compare two caller-supplied text source snapshots and report hashes/diff")
    webkit = parser.add_mutually_exclusive_group()
    webkit.add_argument("--webkit-snapshot", type=Path, help="classify a CSSFontFace snapshot manifest")
    webkit.add_argument("--webkit-compare", nargs=2, type=Path, metavar=("BEFORE", "AFTER"),
                        help="compare two CSSFontFace snapshot manifests")
    webkit.add_argument("--fetch-webkit", metavar="COMMIT", help="download two pinned official source files from an audited full commit")
    parser.add_argument("--snapshot-dir", type=Path, help="new source directory required by --fetch-webkit")
    parser.add_argument("--browser-diagnostic", nargs="+", type=Path,
                        help="import 1-64 passive diagnostic JSON records; no console connection")
    parser.add_argument("--target-firmware", default="14.10", help="self-reported firmware label filter")
    args = parser.parse_args(argv)
    if not args.root.is_dir():
        parser.error("--root must be a directory")
    if args.evidence_root and not args.evidence_root.is_dir():
        parser.error("--evidence-root must be a directory")
    if args.probe_audit and not args.probe_audit.is_dir():
        parser.error("--probe-audit must be a directory")
    webkit_mode = args.webkit_snapshot or args.webkit_compare or args.fetch_webkit
    if sum(bool(mode) for mode in (args.compare, args.probe_audit, webkit_mode, args.browser_diagnostic)) > 1:
        parser.error("choose one comparison/audit mode")
    if args.snapshot_dir and not args.fetch_webkit:
        parser.error("--snapshot-dir requires --fetch-webkit")
    if args.browser_diagnostic:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
        from ps5fwlab.browser_evidence import analyze_diagnostics, render_diagnostics
        try:
            result = analyze_diagnostics(args.browser_diagnostic, args.target_firmware)
            payload = json.dumps(result, indent=2) + "\n" if args.format == "json" else render_diagnostics(result)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                with args.output.open("x", encoding="utf-8") as stream:
                    stream.write(payload)
            else:
                print(payload, end="")
        except (OSError, ValueError) as exc:
            parser.error(str(exc))
        return 0
    if webkit_mode:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
        from ps5fwlab.webkit_patch import classify_snapshot, compare_snapshots, fetch_snapshot, render_report
        if args.output and args.output.exists():
            parser.error("output exists; choose a new output path")
        if args.fetch_webkit:
            if not args.snapshot_dir:
                parser.error("--fetch-webkit requires --snapshot-dir")
            try:
                manifest = fetch_snapshot(args.fetch_webkit, args.snapshot_dir)
            except (OSError, ValueError) as exc:
                parser.error(str(exc))
            result = classify_snapshot(manifest)
        elif args.webkit_compare:
            result = compare_snapshots(*args.webkit_compare)
        else:
            result = classify_snapshot(args.webkit_snapshot)
        payload = json.dumps(result, indent=2) + "\n" if args.format == "json" else render_report(result)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(payload)
        else:
            print(payload, end="")
        return 0
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
    if args.probe_audit:
        probe_report = audit_external_probes(args.probe_audit, args.probe_repo_url)
        payload = json.dumps(probe_report, indent=2) + "\n" if args.format == "json" else render_probe_audit(probe_report)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(payload)
        else:
            print(payload, end="")
        return 0
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
