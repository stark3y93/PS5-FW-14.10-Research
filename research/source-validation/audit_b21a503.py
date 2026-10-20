"""Record bounded source and build-option facts for WebKit b21a503.

This is static PC analysis of public source. It cannot determine PS5 binaries.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import ZipFile

PREFIX = "WebKit-1400/WebKit-1400/"
ZIP = Path("artifacts/sony-oss/WebKit_1400.zip")
PHASE = "Source/JavaScriptCore/dfg/DFGStoreBarrierInsertionPhase.cpp"
COMMIT = "b21a503b579a8ab14c839f82cc77176e507352e5"
PARENT = "1348ad620797f30b9916bbd40423969fa4a8c1cd"


def line_hits(source: str, marker: str) -> list[int]:
    return [number for number, line in enumerate(source.splitlines(), 1) if marker in line]


def main() -> None:
    with ZipFile(ZIP) as archive:
        read = lambda path: archive.read(PREFIX + path).decode("utf-8", "replace")
        sony_phase = read(PHASE)
        config = read("Source/cmake/OptionsPlayStation.cmake")
        features = read("Source/cmake/WebKitFeatures.cmake")
        phi = read("Source/JavaScriptCore/dfg/DFGPhiChildren.h")
        interpreter = read("Source/JavaScriptCore/dfg/DFGAbstractInterpreter.h")
        jsc_calls = []
        for entry in archive.infolist():
            if not entry.filename.startswith(PREFIX + "Source/JavaScriptCore/") or not entry.filename.endswith((".cpp", ".h")):
                continue
            content = archive.read(entry).decode("utf-8", "replace")
            hits = line_hits(content, "forAllTransitiveIncomingValues")
            if hits:
                jsc_calls.append({"path": entry.filename[len(PREFIX):], "lines": hits})
        # Limit the override scan to source/build metadata, not compiled outputs.
        override_files = []
        for entry in archive.infolist():
            path = entry.filename[len(PREFIX):] if entry.filename.startswith(PREFIX) else ""
            if not path or not path.endswith((".cmake", ".json", ".sh", ".ps1", ".py", ".txt", ".xcconfig")):
                continue
            if not (path.startswith("Source/cmake/") or "PlayStation" in path or "CMakePreset" in path):
                continue
            hits = line_hits(archive.read(entry).decode("utf-8", "replace"), "ENABLE_DFG_JIT")
            if hits:
                override_files.append({"path": path, "lines": hits})
    url = f"https://raw.githubusercontent.com/WebKit/WebKit/{PARENT}/{PHASE}"
    with urlopen(url, timeout=45) as response:
        parent = response.read().decode("utf-8", "replace")
    api = f"https://api.github.com/repos/WebKit/WebKit/commits/{COMMIT}"
    with urlopen(Request(api, headers={"User-Agent": "ps5-source-validation"}), timeout=45) as response:
        patch = json.load(response)
    assert patch["parents"][0]["sha"] == PARENT
    report = {
        "scope": "selected public Sony WebKit source and upstream patch; no firmware binary, actual build flags, or console",
        "upstream_commit": COMMIT,
        "upstream_parent": PARENT,
        "upstream_message": patch["commit"]["message"].splitlines()[0],
        "upstream_files": [{"path": f["filename"], "additions": f["additions"], "deletions": f["deletions"]} for f in patch["files"]],
        "upstream_patch_url": f"https://github.com/WebKit/WebKit/commit/{COMMIT}",
        "apple_advisory_url": "https://support.apple.com/en-us/125884",
        "sony_phase_sha256": hashlib.sha256(sony_phase.encode()).hexdigest(),
        "sony_phase_guard": line_hits(sony_phase, "#if ENABLE(DFG_JIT)"),
        "sony_phase_direct_epoch": line_hits(sony_phase, "node->setEpoch(Epoch())"),
        "sony_phase_stack_direct_epoch": line_hits(sony_phase, "entry.value->setEpoch(Epoch())"),
        "sony_phase_transitive_call": line_hits(sony_phase, "forAllTransitiveIncomingValues"),
        "upstream_parent_direct_epoch_count": len(line_hits(parent, "node->setEpoch(Epoch())")),
        "upstream_parent_stack_direct_epoch_count": len(line_hits(parent, "entry.value->setEpoch(Epoch())")),
        "sony_phi_helper": line_hits(phi, "forAllTransitiveIncomingValues"),
        "sony_interpreter_accessor": line_hits(interpreter, "PhiChildren* phiChildren()"),
        "sony_port_defaults": {name: line_hits(config, f"WEBKIT_OPTION_DEFAULT_PORT_VALUE({name} PRIVATE OFF)") for name in ("ENABLE_JIT", "ENABLE_DFG_JIT", "ENABLE_FTL_JIT")},
        "feature_dependency_lines": {name: line_hits(features, f"WEBKIT_OPTION_DEPEND({name}") for name in ("ENABLE_DFG_JIT", "ENABLE_FTL_JIT")},
        "jsc_transitive_helper_references": jsc_calls,
        "dfg_option_metadata_scan": override_files,
        "interpretation": "The pre-fix phase logic is present in published source, but the PlayStation port defaults DFG and JIT off. Actual firmware build flags and equivalent runtime fixes remain unknown.",
    }
    output = Path("notes/b21a503-context-2026-10-20.json")
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Audited {len(jsc_calls)} JSC files referring to transitive helper; {output}")


if __name__ == "__main__":
    main()
