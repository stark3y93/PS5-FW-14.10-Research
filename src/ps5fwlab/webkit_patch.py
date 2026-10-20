"""Conservative CSSFontFace source comparison. No C++ or browser code is executed."""
from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import urllib.request

CSS_PATH = "Source/WebCore/css/CSSFontFace.cpp"
FONT_PATH = "Source/WebCore/css/FontFace.cpp"
PATHS = (CSS_PATH, FONT_PATH)
MAX_SOURCE_BYTES = 2 * 1024 * 1024
PATCHED = "PATCHED — VERIFIED"
VULNERABLE = "VULNERABLE IMPLEMENTATION — VERIFIED"
AMBIGUOUS = "MODIFIED / AMBIGUOUS"
MISSING = "COMPONENT NOT FOUND"
INSUFFICIENT = "INSUFFICIENT EVIDENCE"


def reference_catalog():
    return json.loads(Path(__file__).with_name("webkit_reference_catalog.json").read_text(encoding="utf-8"))["references"]


def _code_only(text):
    # Preserve offsets/newlines so source citations remain valid. This is a
    # limited lexical filter, not a C++ parser; unknown full-file hashes cannot
    # receive a verified verdict even if their function text looks familiar.
    pattern = r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
    return re.sub(pattern, lambda m: "".join("\n" if c == "\n" else " " for c in m[0]), text)


def _function(text, name):
    code = _code_only(text)
    pattern = r"\bvoid\s+iterateClients\s*\(" if name == "iterateClients" else r"\bFontFace::loadForBindings\s*\("
    starts = list(re.finditer(pattern, code))
    if len(starts) != 1:
        return {"state": "unrecognized", "line": None, "body": None}
    start = starts[0].start()
    paren = code.index("(", start)
    depth, end = 1, paren + 1
    while end < len(code) and depth:
        depth += (code[end] == "(") - (code[end] == ")")
        end += 1
    brace = code.find("{", end)
    if depth or brace < 0 or ";" in code[end:brace]:
        return {"state": "incomplete", "line": text.count("\n", 0, start) + 1, "body": None}
    depth, end = 1, brace + 1
    while end < len(code) and depth:
        depth += (code[end] == "{") - (code[end] == "}")
        end += 1
    if depth or code.count("{") != code.count("}"):
        return {"state": "incomplete", "line": text.count("\n", 0, start) + 1, "body": None}
    body = re.sub(r"\s+", "", code[brace + 1:end - 1]).replace("CSSFontFace::Client", "CSSFontFaceClient")
    return {"state": "unrecognized", "line": text.count("\n", 0, start) + 1,
            "body": body, "body_sha256": hashlib.sha256(body.encode()).hexdigest()}


def inspect_functions(css, font):
    iteration = _function(css, "iterateClients")
    prefix = "for(auto&client:copyToVectorOf<Ref<CSSFontFaceClient>>(clients))"
    states = {prefix + "callback(client);": "unguarded",
              prefix + "{if(clients.contains(client))callback(client);}": "guarded"}
    if iteration["state"] != "incomplete":
        iteration["state"] = states.get(iteration.get("body"), "unrecognized")
    load = _function(font, "loadForBindings")
    prefix, suffix = "m_mayLoadedPromiseBeScriptObservable=true;", "returnm_loadedPromise.get();"
    states = {prefix + "m_backing->load();" + suffix: "unprotected",
              prefix + "protect(m_backing)->load();" + suffix: "pinned"}
    if load["state"] != "incomplete":
        load["state"] = states.get(load.get("body"), "unrecognized")
    # Bodies are deliberately omitted from reports; states and line/hash citations
    # suffice without redistributing whole vendor source files.
    for entry in (iteration, load):
        entry.pop("body", None)
    return {"client_iteration": {"file": CSS_PATH, **iteration},
            "backing_load": {"file": FONT_PATH, **load}}


def classify_snapshot(manifest_path, references=None):
    """Verify source bytes against a manifest and an audited reference catalog.

    Source classification and firmware attribution are separate. This utility
    cannot validate signed Sony build provenance, so its PS5 verdict stays
    insufficient even when a manifest claims a version or target mapping.
    """
    references = reference_catalog() if references is None else references
    path = Path(manifest_path)
    report = {"classification": INSUFFICIENT, "scope": "source snapshot only",
              "ps5_1410_classification": INSUFFICIENT, "reasons": [], "files": [],
              "functions": {}, "reference_matches": [], "provenance": {}}
    try:
        if path.stat().st_size > 256 * 1024:
            raise ValueError("manifest exceeds 256 KiB")
        raw_manifest = path.read_bytes()
        manifest = json.loads(raw_manifest)
        pending = [(manifest, 0)]
        while pending:
            value, depth = pending.pop()
            if depth > 16:
                raise ValueError("manifest nesting exceeds 16 levels")
            if isinstance(value, dict):
                pending.extend((item, depth + 1) for item in value.values())
            elif isinstance(value, list):
                pending.extend((item, depth + 1) for item in value)
        if not isinstance(manifest, dict) or manifest.get("schema_version") != 1 or not isinstance(manifest.get("files"), list):
            raise ValueError("expected snapshot schema_version 1 and files list")
        if not isinstance(manifest.get("provenance", {}), dict):
            raise ValueError("provenance must be an object")
        report.update(label=manifest.get("label", "unnamed"),
                      provenance=manifest.get("provenance", {}),
                      manifest_sha256=hashlib.sha256(raw_manifest).hexdigest())
        entries = {}
        for entry in manifest["files"]:
            if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
                raise ValueError("each source entry requires a path string")
            name = entry["path"]
            pure = PurePosixPath(name)
            if pure.is_absolute() or ".." in pure.parts or "\\" in name or ":" in name:
                raise ValueError("snapshot paths must stay inside their directory")
            if name in entries:
                raise ValueError("duplicate snapshot file")
            entries[name] = entry
        contents, digests = {}, {}
        for name in PATHS:
            p = path.parent / name
            if not p.resolve().is_relative_to(path.parent.resolve()):
                raise ValueError("snapshot symlink escapes its directory")
            if name not in entries or not p.is_file():
                continue
            if p.stat().st_size > MAX_SOURCE_BYTES:
                raise ValueError("source exceeds 2 MiB")
            raw = p.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            expected = entries[name].get("sha256")
            verified = bool(re.fullmatch(r"[a-f0-9]{64}", str(expected))) and digest == expected
            report["files"].append({"path": name, "sha256": digest, "expected_sha256": expected,
                                    "hash_verified": verified, "bytes": len(raw),
                                    "origin_url": entries[name].get("origin_url")})
            if not verified:
                raise ValueError(f"source SHA-256 mismatch or missing pin: {name}")
            contents[name] = raw.decode("utf-8")
            digests[name] = digest
        if not contents:
            report["classification"] = MISSING
            report["reasons"].append("Neither required source file is available.")
            return report
        if len(contents) != 2:
            raise ValueError("Both CSSFontFace.cpp and FontFace.cpp are required")
        report["functions"] = inspect_functions(contents[CSS_PATH], contents[FONT_PATH])
        if any(v["state"] == "incomplete" for v in report["functions"].values()):
            raise ValueError("Incomplete function or unbalanced source file")
        matches = [ref for ref in references if ref["files"] == digests]
        report["reference_matches"] = [{"revision": ref["revision"], "label": ref["label"]} for ref in matches]
        revision = report["provenance"].get("revision")
        claimed = next((ref for ref in references if ref["revision"] == revision), None)
        if claimed and claimed["files"] != digests:
            raise ValueError("Asserted reference revision disagrees with the source file hashes")
        state = tuple(report["functions"][key]["state"] for key in ("client_iteration", "backing_load"))
        if matches and state == ("guarded", "pinned"):
            report["classification"] = PATCHED
        elif matches and state == ("unguarded", "unprotected"):
            report["classification"] = VULNERABLE
        else:
            report["classification"] = AMBIGUOUS
        if not matches:
            report["reasons"].append("Full source pair is not an audited reference; familiar snippets alone are insufficient.")
        if state == ("unguarded", "pinned"):
            report["reasons"].append("Lifetime pin present; membership guard absent. This includes a documented security backport; do not call it an unpatched UAF.")
        report["reasons"].append("No exact PS5 14.10 executable/build correspondence is validated by this source-only tool.")
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, RecursionError) as exc:
        report["classification"] = INSUFFICIENT
        report["reasons"].append(str(exc))
    return report


def compare_snapshots(before, after, references=None):
    left = classify_snapshot(before, references)
    right = classify_snapshot(after, references)
    changes = []
    for name in sorted(set(left["functions"]) | set(right["functions"])):
        a,b = left["functions"].get(name),right["functions"].get(name)
        if a != b:
            changes.append({"function": name, "before": a, "after": b})
    return {"scope": "source comparison only", "before": left, "after": right,
            "function_changes": changes, "ps5_1410_classification": INSUFFICIENT}


class NoSourceRedirect(urllib.request.HTTPRedirectHandler):
    """Reject before urllib constructs or contacts a redirect destination."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("source download redirects are forbidden")


def fetch_snapshot(revision, destination, references=None, opener=None):
    """Fetch only an audited full commit from official WebKit raw URLs; never overwrite."""
    references = reference_catalog() if references is None else references
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError("snapshot destination already exists")
    ref = next((r for r in references if r["revision"] == revision), None)
    if not re.fullmatch(r"[a-f0-9]{40}", revision) or ref is None:
        raise ValueError("download requires an audited full WebKit commit SHA")
    opener = opener or urllib.request.build_opener(NoSourceRedirect()).open
    downloaded, entries = {}, []
    for name in PATHS:
        url = f"https://raw.githubusercontent.com/WebKit/WebKit/{revision}/{name}"
        with opener(url, timeout=40) as response:
            raw = response.read(MAX_SOURCE_BYTES + 1)
            if response.geturl() != url:
                raise ValueError("unexpected download redirect")
        if len(raw) > MAX_SOURCE_BYTES or hashlib.sha256(raw).hexdigest() != ref["files"][name]:
            raise ValueError(f"download failed pinned SHA-256 verification: {name}")
        downloaded[name] = raw
        entries.append({"path": name, "sha256": ref["files"][name], "origin_url": url})
    destination.mkdir(parents=True)
    for name, raw in downloaded.items():
        p = destination / name
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("xb") as stream:
            stream.write(raw)
    manifest = {"schema_version": 1, "label": ref["label"], "files": entries,
                "provenance": {"kind": "upstream-source", "revision": revision,
                               "acquired_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                               "source_url": f"https://github.com/WebKit/WebKit/commit/{revision}"}}
    path = destination / "snapshot.json"
    with path.open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2)
        stream.write("\n")
    return path


def render_report(report):
    lines = ["# CSSFontFace source evidence report", "",
             "Scope: source snapshots. PS5 14.10 classification: **INSUFFICIENT EVIDENCE**.", ""]
    pairs = [("Before", report["before"]),("After",report["after"])] if "before" in report else [("Snapshot",report)]
    for title, item in pairs:
        lines += [f"## {title}: {item.get('label', 'unavailable')}", "",
                  f"Source classification: **{item['classification']}**", "",
                  f"Manifest SHA-256: `{item.get('manifest_sha256', 'unavailable')}`", ""]
        for f in item["files"]:
            lines.append(f"- `{f['path']}` — SHA-256 `{f['sha256']}`; hash verified: {f['hash_verified']}; origin: {f['origin_url'] or 'not recorded'}")
        lines.append("")
        for name, f in item["functions"].items():
            lines.append(f"- {name}: **{f['state']}** at `{f['file']}:{f['line']}`")
        lines += [""] + [f"- {reason}" for reason in item["reasons"]] + [""]
    lines += ["A verified source pattern does not establish firmware applicability, reachability, a runtime fault, or exploitability.",
              "Caller-provided target/version labels and hashes identify claims and bytes; they do not authenticate a Sony firmware build."]
    return "\n".join(lines) + "\n"


def model_client_iteration(clients, actions, membership_guard):
    """Ordered synthetic snapshot model; WeakHashSet's actual order is unspecified."""
    live = list(clients)
    snapshot = list(live)
    callbacks, removed_callbacks = [], []
    for client in snapshot:
        if membership_guard and client not in live:
            continue
        if client not in live:
            removed_callbacks.append(client)
        callbacks.append(client)
        for removed in actions.get(client, {}).get("remove", []):
            if removed in live:
                live.remove(removed)
        for added in actions.get(client, {}).get("add", []):
            if added not in live:
                live.append(added)
    return {"callbacks": callbacks, "callbacks_after_removal": removed_callbacks, "live_clients": live}


def model_load_lifetime(pin_backing):
    """Logical reference-count model; no unsafe pointer or real heap corruption."""
    owners = 1 + int(pin_backing)
    owners -= 1  # Reentrant callback releases/replaces the owning backing member.
    alive = owners > 0
    if pin_backing:
        owners -= 1  # Temporary strong reference ends when load returns.
    return {"alive_when_load_resumes": alive, "owners_after_return": owners,
            "limitation": "Synthetic ownership sequence, not WebKit or PS5 execution."}
