"""Offline capability observations, never vulnerability or target authentication."""
import hashlib
import html
import json
import re
from pathlib import Path

SCHEMA = "ps5-browser-diagnostic/1"
FEATURES = {"Promise", "Map", "Set", "Symbol", "BigInt", "WebAssembly", "ArrayBuffer",
            "Uint8Array", "TextEncoder", "FontFace", "fontSet", "cssGrid", "cssFontFamily", "TransformStream",
            "secureContext"}
STAGES = ("browser_page", "native_userland", "sandbox_transition", "kernel_access",
          "hypervisor_access", "firmware_mapping", "independent_reproduction")
ALLOWED = {"schema", "diagnostic_version", "status", "firmware_label", "captured_at",
           "user_agent", "features"}


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _depth(value, depth=0):
    if depth > 12:
        raise ValueError("JSON nesting exceeds 12")
    if isinstance(value, dict):
        for item in value.values():
            _depth(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            _depth(item, depth + 1)


def _firmware(value):
    return isinstance(value, str) and re.fullmatch(r"\d{1,2}\.\d{2}", value) is not None


def _read_record(path):
    path = Path(path)
    result = {"file": str(path), "status": "invalid", "warnings": [],
              "sha256": None, "evidence": {"file": str(path), "pointer": "/features"}}
    try:
        with path.open("rb") as stream:
            raw = stream.read(65537)
        if len(raw) > 65536:
            raise ValueError("record exceeds 65536 bytes")
        result["sha256"] = hashlib.sha256(raw).hexdigest()
        data = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=_pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
        _depth(data)
        if not isinstance(data, dict) or data.get("schema") != SCHEMA:
            raise ValueError("wrong schema or root")
        for key, bound in (("diagnostic_version", 32), ("captured_at", 64), ("user_agent", 1024)):
            if not isinstance(data.get(key), str) or len(data[key]) > bound:
                raise ValueError("missing, invalid or oversized " + key)
        if data["diagnostic_version"] != "1.0":
            raise ValueError("unsupported diagnostic version")
        if not _firmware(data.get("firmware_label")):
            raise ValueError("firmware label must be e.g. 14.10")
        if data.get("status") not in ("complete", "started", "error"):
            raise ValueError("invalid status")
        features = data.get("features")
        if not isinstance(features, dict) or not features or len(features) > len(FEATURES):
            raise ValueError("invalid features")
        if any(k not in FEATURES or not (type(v) is bool or v == "error" and type(v) is str)
               for k, v in features.items()):
            raise ValueError("invalid feature name or value")
        result.update(status="complete" if data["status"] == "complete" else "incomplete",
                      firmware_label=data["firmware_label"], features=features,
                      captured_at=data["captured_at"], user_agent=data["user_agent"])
        if set(data) - ALLOWED:
            result["warnings"].append("unsupported-claim-fields")
        ua_fw = re.search(r"PlayStation\s*5/([0-9]+\.[0-9]{2})", data["user_agent"], re.I)
        if ua_fw and ua_fw[1] != data["firmware_label"]:
            result["warnings"].append("ua-firmware-disagrees")
        if not ua_fw:
            result["warnings"].append("ua-not-ps5")
    except (OSError, ValueError, UnicodeError, RecursionError) as exc:
        result["error"] = str(exc)
    return result


def analyze_diagnostics(paths, target_firmware="14.10"):
    """Accept local JSON, retain provenance, and compare eligible observations only.

    Firmware labels and capture times are self-reported. JSON pointers address the
    exact hashed file; a hash does not prove a device, author, time or build.
    """
    if not _firmware(target_firmware):
        raise ValueError("target firmware must be e.g. 14.10")
    paths = list(paths)
    if not paths or len(paths) > 64:
        raise ValueError("supply 1 to 64 diagnostic records")
    records, seen, observations = [], set(), {}
    for path in paths:
        record = _read_record(path)
        records.append(record)
        digest = record["sha256"]
        if digest and digest in seen:
            record["warnings"].append("duplicate-content")
        if digest:
            seen.add(digest)
        if record.get("firmware_label") != target_firmware:
            record["warnings"].append("firmware-label-mismatch")
        if (record["status"] != "complete" or record.get("firmware_label") != target_firmware
                or any(w in record["warnings"] for w in
                       ("duplicate-content", "ua-firmware-disagrees", "ua-not-ps5"))):
            continue
        for feature, value in record["features"].items():
            if type(value) is bool:
                observations.setdefault(feature, []).append({"value": value, "file": record["file"],
                    "sha256": digest, "pointer": "/features/" + feature})
    contradictions = [{"feature": key, "classification": "OBSERVATION CONFLICT — CAUSE UNKNOWN", "evidence": rows}
                      for key, rows in sorted(observations.items()) if {r["value"] for r in rows} == {True, False}]
    boundaries = [{"stage": stage, "status": "UNPROVEN",
                   "reason": "Capability data cannot establish this boundary."} for stage in STAGES]
    if observations:
        boundaries[0].update(status="SELF-REPORTED PAGE COMPLETION",
                             reason="At least one matching-label JSON record reports completion; origin unauthenticated.")
    return {"schema": "ps5-browser-evidence/1", "target_firmware": target_firmware,
            "target_authenticated": False, "vulnerability_verdict": "INSUFFICIENT EVIDENCE",
            "records": records, "contradictions": contradictions, "boundaries": boundaries,
            "next_investigations": [
                {"rank": 1, "task": "Obtain authorized exact-firmware browser build/source correspondence",
                 "value": "Can settle target patch compatibility; capabilities cannot."},
                {"rank": 2, "task": "Collect a passive diagnostic with firmware-screen and navigation context",
                 "value": "Can establish API reachability; cannot prove memory corruption."},
                {"rank": 3, "task": "Run pinned old/fixed WebKit regression on a prepared PC engine",
                 "value": "Can test upstream behavior; cannot authenticate Sony production code."}],
            "limits": ["No hardware or build authentication", "No exploit or memory corruption test",
                       "API absence can reflect context restrictions", "Ranks are research priorities, not exploit probabilities"]}


def _cell(value):
    escaped = html.escape(str(value), quote=True).replace("\r", " ").replace("\n", " ")
    # Entity-encode Markdown delimiters too: HTML escaping alone permits images,
    # links and inline formatting in attacker-controlled filenames/error strings.
    return "".join("&#" + str(ord(c)) + ";" if c in "\\`*_[]()!|" else c for c in escaped)


def render_diagnostics(report):
    lines = ["# Browser diagnostic evidence", "", "Target label: " + _cell(report["target_firmware"]), "",
             "Vulnerability verdict: **INSUFFICIENT EVIDENCE**. Hardware/firmware identity is unauthenticated.", "",
             "| File | Record state | SHA-256 | Warnings |", "|---|---|---|---|"]
    for row in report["records"]:
        lines.append("| " + " | ".join(_cell(v) for v in
                     (row["file"], row["status"], row["sha256"], ", ".join(row["warnings"]))) + " |")
        if "error" in row:
            lines.extend(["", "Input rejected: " + _cell(row["error"]), ""])
    lines.extend(["", "## Boundary matrix", "", "| Stage | Status | Reason |", "|---|---|---|"])
    for row in report["boundaries"]:
        lines.append("| " + " | ".join(_cell(row[k]) for k in ("stage", "status", "reason")) + " |")
    lines.extend(["", "## Observation conflicts", ""])
    for conflict in report["contradictions"]:
        lines.append("- " + _cell(conflict["feature"]) + ": " + _cell(conflict["classification"]))
        for evidence in conflict["evidence"]:
            lines.append("  - " + _cell(evidence["file"]) + " " + _cell(evidence["pointer"]) +
                         " = " + str(evidence["value"]) + "; SHA-256 " + evidence["sha256"])
    if not report["contradictions"]:
        lines.append("No eligible conflicting observations.")
    lines.extend(["", "## Next investigations", ""])
    for row in report["next_investigations"]:
        lines.append(str(row["rank"]) + ". " + row["task"] + ": " + row["value"])
    lines.extend(["", "## Limits", ""] + ["- " + s for s in report["limits"]])
    return "\n".join(lines) + "\n"
