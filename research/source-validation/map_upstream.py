"""Hash selected Sony WebKit files against pinned, public upstream revisions.

No firmware, console, or executable is accessed. The Sony archive remains ignored.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

SONY_ZIP = Path("artifacts/sony-oss/WebKit_1400.zip")
PREFIX = "WebKit-1400/WebKit-1400/"
WEBKIT_TAG = "WebKit-7616.1.27.211.1"
WEBKIT_TAG_OBJECT = "cc47db7e0acf86175cf5b704a8802b20df5d80aa"
WEBKIT_COMMIT = "0e722583a4d695c7b25f384c61fbf5b59b4c3146"
FILES = [
    "Configurations/Version.xcconfig",
    "Source/JavaScriptCore/dfg/DFGStoreBarrierInsertionPhase.cpp",
    "Source/JavaScriptCore/dfg/DFGPhiChildren.h",
    "Source/WTF/wtf/Vector.h",
    "Source/WebCore/dom/Document.cpp",
    "Source/WebKit/WebProcess/WebPage/WebPage.cpp",
    "Source/cmake/OptionsPlayStation.cmake",
]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    refs = subprocess.check_output(
        ["git", "ls-remote", "--tags", "https://github.com/WebKit/WebKit.git", WEBKIT_TAG + "*"],
        text=True, timeout=45,
    )
    parsed = dict(line.split("\t", 1)[::-1] for line in refs.splitlines())
    assert parsed[f"refs/tags/{WEBKIT_TAG}"] == WEBKIT_TAG_OBJECT
    assert parsed[f"refs/tags/{WEBKIT_TAG}^{{}}"] == WEBKIT_COMMIT
    rows = []
    with ZipFile(SONY_ZIP) as sony:
        for path in FILES:
            local = sony.read(PREFIX + path)
            url = f"https://raw.githubusercontent.com/WebKit/WebKit/{WEBKIT_COMMIT}/{path}"
            with urlopen(url, timeout=45) as response:
                upstream = response.read()
            rows.append({
                "path": path,
                "sony_bytes": len(local), "sony_sha256": digest(local),
                "upstream_bytes": len(upstream), "upstream_sha256": digest(upstream),
                "byte_identical": local == upstream, "upstream_url": url,
            })
    report = {
        "scope": "selected independent files only; byte equality does not date the entire archive or any firmware binary",
        "sony_archive": str(SONY_ZIP),
        "sony_official_index": "https://www.playstation.com/en-us/oss/ps5/webkit/",
        "upstream_tag": WEBKIT_TAG,
        "upstream_tag_object": WEBKIT_TAG_OBJECT,
        "upstream_peeled_commit": WEBKIT_COMMIT,
        "method": "SHA-256 of unmodified ZIP member bytes and pinned WebKit raw Git files",
        "files": rows,
    }
    output = Path("notes/upstream-file-map-2026-10-20.json")
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{sum(r['byte_identical'] for r in rows)}/{len(rows)} files byte-identical; {output}")


if __name__ == "__main__":
    main()
