"""Incremental, provenance-preserving GitHub source tracking.

The updater records upstream activity as observations. It never turns an
upstream README, issue, release, or commit into a verified vulnerability or
firmware-compatibility statement.
"""
from __future__ import annotations

import hashlib
import json
import os
import html
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

API = "https://api.github.com"
UNVERIFIED = "UNVERIFIED_SOURCE_ACTIVITY"


def canonical_repo(url_or_name: str) -> str:
    value = url_or_name.strip().rstrip("/").removesuffix(".git").rstrip("/")
    if value.startswith("https://github.com/"):
        value = value.removeprefix("https://github.com/")
    elif value.startswith("http://github.com/"):
        value = value.removeprefix("http://github.com/")
    parts = value.split("/")
    if len(parts) != 2 or any(not p or p in {".", ".."} for p in parts):
        raise ValueError(f"expected a GitHub owner/repository: {url_or_name!r}")
    return "/".join(part.lower() for part in parts)


def deduplicate_projects(projects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate project records by normalized repository identity.

    A duplicate keeps the first stable id and merges categories; conflicting
    license or commit pins are rejected so source identity cannot be silently
    overwritten.
    """
    result: dict[str, dict[str, Any]] = {}
    ids: dict[str, str] = {}
    for original in projects:
        row = dict(original)
        key = canonical_repo(row.get("url") or row.get("full_name", ""))
        project_id = row.get("id")
        if not project_id:
            raise ValueError("project id is required")
        prior_key = ids.get(project_id)
        if prior_key is not None and prior_key != key:
            raise ValueError(f"project id {project_id!r} maps to multiple repositories")
        ids[project_id] = key
        if key not in result:
            row["canonical_url"] = f"https://github.com/{key}"
            row["categories"] = sorted(set(row.get("categories", [])))
            result[key] = row
            continue
        prior = result[key]
        for field in ("commit", "license"):
            left, right = prior.get(field), row.get(field)
            if left and right and left != right:
                raise ValueError(f"conflicting {field} values for {key}")
            if not left and right:
                prior[field] = right
        prior["categories"] = sorted(set(prior.get("categories", [])) | set(row.get("categories", [])))
        if row.get("summary") and row["summary"] not in prior.get("summary", ""):
            prior["summary"] = (prior.get("summary", "") + " " + row["summary"]).strip()
    return sorted(result.values(), key=lambda x: x["canonical_url"])


def validate_compatibility_claim(claim: dict[str, Any]) -> None:
    """Enforce evidence labels; a verified label requires explicit reproduction."""
    classes = {"source_code", "project_documentation", "vendor_advisory", "independent_test", "third_party_report"}
    statuses = {"author_reported", "source_observed", "independently_reproduced", "unknown", "contradicted"}
    if claim.get("evidence_class") not in classes:
        raise ValueError(f"unsupported evidence class: {claim.get('evidence_class')!r}")
    if claim.get("status") not in statuses:
        raise ValueError(f"unsupported evidence status: {claim.get('status')!r}")
    if claim["status"] == "independently_reproduced":
        if claim["evidence_class"] != "independent_test" or not claim.get("reproduction_record"):
            raise ValueError("independent verification requires independent_test evidence and a reproduction record")
    if not claim.get("source_url", "").startswith("https://"):
        raise ValueError("compatibility claim requires an HTTPS source URL")
    if not claim.get("pinned_commit"):
        raise ValueError("compatibility claim requires a pinned source commit")
    if not claim.get("firmware_scope"):
        raise ValueError("use an explicit firmware range or 'not stated'; never infer a range")


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _request_json(url: str, token: str | None = None) -> tuple[int, Any, dict[str, str]]:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "ps5-research-source-tracker"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return response.status, json.loads(response.read()), dict(response.headers.items())
    except urllib.error.HTTPError as error:
        if error.code == 304:
            return 304, None, dict(error.headers.items())
        raise


def _pages(url: str, token: str | None, request_json: Callable[..., tuple[int, Any, dict[str, str]]]) -> list[Any]:
    result: list[Any] = []
    current = url
    page_count = 0
    while current:
        page_count += 1
        if page_count > 100:
            raise ValueError("GitHub API pagination exceeded the 100-page safety bound")
        if urllib.parse.urlparse(current).scheme != "https" or urllib.parse.urlparse(current).netloc != "api.github.com":
            raise ValueError("refusing to follow pagination outside https://api.github.com")
        status, data, headers = request_json(current, token)
        if status == 304:
            break
        if not isinstance(data, list):
            raise ValueError(f"expected a GitHub API list response from {current}")
        result.extend(data)
        link = headers.get("Link", headers.get("link", ""))
        current = ""
        for item in link.split(","):
            if 'rel="next"' in item:
                current = item[item.find("<") + 1:item.find(">")]
                break
    return result


def _releases_since(url: str, since: str, known_ids: set[str], token: str | None,
                    request_json: Callable[..., tuple[int, Any, dict[str, str]]]) -> list[dict[str, Any]]:
    """Read newest releases and stop at the saved ID/time boundary."""
    result: list[dict[str, Any]] = []
    current = url
    pages = 0
    while current:
        pages += 1
        if pages > 100:
            raise ValueError("GitHub release pagination exceeded the 100-page safety bound")
        parsed = urllib.parse.urlparse(current)
        if parsed.scheme != "https" or parsed.netloc != "api.github.com":
            raise ValueError("refusing to follow release pagination outside https://api.github.com")
        status, data, headers = request_json(current, token)
        if status == 304:
            break
        if not isinstance(data, list):
            raise ValueError("expected a GitHub releases list response")
        stop = False
        for row in data:
            if str(row.get("id")) in known_ids:
                stop = True
                break
            date = row.get("published_at") or row.get("created_at") or ""
            if date and date <= since:
                stop = True
                break
            result.append(row)
        if stop:
            break
        link = headers.get("Link", headers.get("link", ""))
        current = ""
        for item in link.split(","):
            if 'rel="next"' in item:
                current = item[item.find("<") + 1:item.find(">")]
                break
    return result


def observation_id(repository: str, event_type: str, external_id: str) -> str:
    raw = f"{canonical_repo(repository)}\0{event_type}\0{external_id}".encode()
    return hashlib.sha256(raw).hexdigest()[:24]


def merge_observations(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Stable upsert by source identity and upstream event id, retaining provenance."""
    merged = {row["id"]: dict(row) for row in existing}
    for row in incoming:
        item = dict(row)
        expected = observation_id(item["repository"], item["event_type"], str(item["external_id"]))
        if item.get("id") not in (None, expected):
            raise ValueError("observation id does not match its source identity")
        item["id"] = expected
        item["classification"] = UNVERIFIED
        previous = merged.get(expected)
        if previous:
            # Activity may be refreshed, but its source identity and first-seen
            # provenance are immutable, and classification cannot be promoted.
            item["first_seen"] = previous.get("first_seen", item.get("first_seen"))
            item["source_url"] = previous["source_url"]
            item["pinned_commit"] = previous.get("pinned_commit") or item.get("pinned_commit")
        else:
            item.setdefault("first_seen", item.get("observed_at"))
        merged[expected] = item
    return sorted(merged.values(), key=lambda x: (x.get("repository", ""), x.get("event_type", ""), str(x.get("external_id", ""))))


def poll_sources(config: dict[str, Any], state: dict[str, Any] | None = None, *, token: str | None = None,
                 now: str | None = None, request_json: Callable[..., tuple[int, Any, dict[str, str]]] = _request_json) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Read-only incremental GitHub REST poll; no full clones and no claim promotion."""
    if config.get("enabled") is not True:
        return state or {"schema_version": 1, "last_checked": None, "sources": {}}, []
    now = now or _iso_now()
    updated = json.loads(json.dumps(state or {"schema_version": 1, "last_checked": None, "sources": {}}))
    updated.setdefault("sources", {})
    incoming: list[dict[str, Any]] = []
    for project in deduplicate_projects(config.get("projects", [])):
        full_name = project["canonical_url"].removeprefix("https://github.com/")
        cursor = updated["sources"].get(full_name, {}).get("last_checked") or (config.get("baseline_date", "1970-01-01") + "T00:00:00Z")
        # Small overlap protects events landing at the timestamp boundary; IDs
        # make this replay harmless.
        try:
            since = (datetime.fromisoformat(cursor.replace("Z", "+00:00")) - timedelta(seconds=1)).isoformat().replace("+00:00", "Z")
        except ValueError as exc:
            raise ValueError(f"invalid source cursor for {full_name}: {cursor}") from exc
        base = f"{API}/repos/{urllib.parse.quote(full_name, safe='/')}"
        _, repo, _ = request_json(base, token)
        default_branch = repo["default_branch"]
        _, latest_commit, _ = request_json(base + "/commits/" + urllib.parse.quote(default_branch, safe=""), token)
        license_now = (repo.get("license") or {}).get("spdx_id") or "NOASSERTION"
        commits = _pages(base + "/commits?" + urllib.parse.urlencode({"sha": default_branch, "since": since, "per_page": 100}), token, request_json)
        known_release_ids = {str(x["external_id"]) for x in updated.get("observations", [])
                             if x.get("repository") == full_name and x.get("event_type") == "release"}
        releases = _releases_since(base + "/releases?per_page=100", since, known_release_ids, token, request_json)
        issue_url = base + "/issues?" + urllib.parse.urlencode({"state": "all", "sort": "updated", "direction": "desc", "since": since, "per_page": 100})
        issues = _pages(issue_url, token, request_json)
        for source_type, rows in (("commit", commits), ("release", releases), ("issue_or_pull_request", issues)):
            for row in rows:
                event_type = source_type
                if source_type == "commit":
                    external_id = row["sha"]
                    title = (row.get("commit", {}).get("message") or "").splitlines()[0]
                    event_url = row.get("html_url")
                    changed_at = row.get("commit", {}).get("committer", {}).get("date")
                    upstream_state = "committed"
                elif source_type == "release":
                    external_id = str(row["id"])
                    title, event_url, changed_at = row.get("name") or row.get("tag_name") or "release", row.get("html_url"), row.get("published_at") or row.get("created_at")
                    upstream_state = "draft" if row.get("draft") else ("prerelease" if row.get("prerelease") else "published")
                else:
                    external_id = str(row["id"])
                    title, event_url, changed_at = row.get("title") or "issue/pull request", row.get("html_url"), row.get("updated_at")
                    upstream_state = row.get("state", "unknown")
                    if row.get("pull_request"):
                        event_type = "pull_request"
                    else:
                        event_type = "issue"
                incoming.append({"repository": full_name, "repository_id": project["id"], "event_type": event_type, "external_id": external_id,
                                 "title": title, "source_url": event_url or project["url"], "observed_at": now,
                                 "upstream_updated_at": changed_at, "upstream_state": upstream_state,
                                 "pinned_commit": row.get("sha") if source_type == "commit" else latest_commit.get("sha"),
                                 "license_at_review": license_now, "classification": UNVERIFIED})
        previous = updated["sources"].get(full_name, {})
        if previous.get("license") and previous["license"] != license_now:
            incoming.append({"repository": full_name, "repository_id": project["id"], "event_type": "license_change",
                             "external_id": f"{previous['license']}->{license_now}:{now}",
                             "title": f"GitHub license metadata changed: {previous['license']} to {license_now}",
                             "source_url": f"https://github.com/{full_name}", "observed_at": now,
                             "upstream_updated_at": now, "upstream_state": "changed", "pinned_commit": latest_commit.get("sha"),
                             "license_at_review": license_now, "classification": UNVERIFIED})
        updated["sources"][full_name] = {"last_checked": now, "head_sha": latest_commit.get("sha"),
                                           "default_branch": default_branch, "license": license_now, "license_checked_at": now,
                                           "latest_release_id": str(releases[0]["id"]) if releases else None}
    candidates = {x["repository_name"]: dict(x) for x in updated.get("discovery_candidates", [])}
    tracked_names = {canonical_repo(project.get("url", "")) for project in config.get("projects", [])}
    for query in config.get("discovery_queries", []):
        url = API + "/search/repositories?" + urllib.parse.urlencode({"q": query, "sort": "updated", "per_page": 30})
        _, result, _ = request_json(url, token)
        for repo in result.get("items", []):
            name = canonical_repo(repo["full_name"])
            if name in tracked_names:
                continue
            prior = candidates.get(name)
            candidates[name] = {"repository_name": name, "url": repo.get("html_url", f"https://github.com/{name}"),
                                "description": repo.get("description") or "", "stars": int(repo.get("stargazers_count") or 0),
                                "pushed_at": repo.get("pushed_at"), "first_seen": prior.get("first_seen", now) if prior else now,
                                "status": "candidate_unreviewed"}
    updated["discovery_candidates"] = sorted(candidates.values(), key=lambda x: x["repository_name"])
    updated["last_checked"] = now
    return updated, merge_observations([], incoming)


def update_files(config_path: str | Path, state_path: str | Path, report_path: str | Path, *, token: str | None = None, enable: bool = False) -> dict[str, int]:
    config_path, state_path, report_path = Path(config_path), Path(state_path), Path(report_path)
    ecosystem = json.loads(config_path.read_text(encoding="utf-8"))
    enabled = enable or ecosystem.get("automation", {}).get("enabled") is True
    if config_path.with_name("catalog.json").exists():
        base_catalog = json.loads(config_path.with_name("catalog.json").read_text(encoding="utf-8"))
        repository_rows = base_catalog.get("repositories", []) + ecosystem.get("repositories", [])
    else:
        repository_rows = ecosystem.get("repositories", [])
    repository_by_id = {row["id"]: row for row in repository_rows}
    tracked_ids = {row["repository_id"] for row in ecosystem.get("projects", [])}
    projects = []
    for repository_id in sorted(tracked_ids):
        repo = repository_by_id.get(repository_id)
        if repo:
            projects.append({"id": repository_id, "url": repo["url"], "commit": repo["commit"], "license": repo["license"]})
    config = {"enabled": enabled, "baseline_date": ecosystem.get("snapshot_date"), "discovery_queries": ecosystem.get("automation", {}).get("discovery_queries", []), "projects": projects}
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else None
    if not enabled:
        return {"sources_checked": 0, "new_observations": 0, "skipped_disabled": 1}
    token = token or os.environ.get("PS5_RESEARCH_GITHUB_TOKEN") or os.environ.get("GITHUB_TOKEN")
    new_state, incoming = poll_sources(config, state, token=token)
    old_rows = state.get("observations", []) if state else []
    all_rows = merge_observations(old_rows, incoming)
    new_state["observations"] = all_rows
    new_state.setdefault("discovery_candidates", [])
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_tmp = state_path.with_suffix(state_path.suffix + ".tmp")
    state_tmp.write_text(json.dumps(new_state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    state_tmp.replace(state_path)
    new_ids = {x["id"] for x in incoming} - {x["id"] for x in old_rows}
    old_candidate_names = {x["repository_name"] for x in (state or {}).get("discovery_candidates", [])}
    new_candidates = [x for x in new_state["discovery_candidates"] if x["repository_name"] not in old_candidate_names]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    changed = [x for x in incoming if x["id"] in new_ids]
    kinds: dict[str, int] = {}
    for item in changed:
        kinds[item["event_type"]] = kinds.get(item["event_type"], 0) + 1
    lines = ["# Upstream research update", "", f"Checked: {new_state['last_checked']}", "",
             f"New upstream activity records: {len(changed)} ({', '.join(f'{n} {k}' for k,n in sorted(kinds.items())) or 'none'}). Tracked repositories: {len(new_state['sources'])}. Discovery candidates retained for review: {len(new_state['discovery_candidates'])}.",
             "", "## Research impact", "", "These observations identify source changes and discovery leads; they do not validate a vulnerability or firmware compatibility. No claim is promoted automatically.",
             "", "**14.10 priority impact:** no priority changes until a reviewer reads the pinned diff and finds version-specific evidence. A repository update or compatibility label is not evidence that a method works on 14.10.", ""]
    for row in changed[:100]:
        safe_title = html.escape(str(row["title"])).replace("[", "&#91;").replace("]", "&#93;").replace("\n", " ")
        safe_url = row["source_url"] if str(row["source_url"]).startswith("https://github.com/") else "https://github.com"
        lines.extend([f"- **{row['repository']} · {row['event_type']} ({row.get('upstream_state') or 'state unknown'})** — [{safe_title}]({safe_url})", f"  Updated: {row.get('upstream_updated_at') or 'unknown'}; evidence status: {row['classification']}. Review the commit/release/issue context and the affected project component."])
    if not changed:
        lines.append("No new upstream activity was returned by the configured incremental queries.")
    if new_candidates:
        lines.extend(["", "## New discovery candidates", "", "These search results are leads only. Repository identity, license, source history and compatibility evidence must be reviewed before adding them to the pinned catalog."])
        for item in new_candidates[:30]:
            title = html.escape(str(item["repository_name"]))
            link = item["url"] if str(item["url"]).startswith("https://github.com/") else "https://github.com"
            description = html.escape(str(item.get("description", ""))).replace("\n", " ")
            lines.append(f"- [{title}]({link}) — {description}; unverified search match, {item.get('stars',0)} stars.")
    lines.extend(["", "A researcher must inspect the pinned source and update a compatibility claim explicitly before any status changes."])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_tmp = report_path.with_suffix(report_path.suffix + ".tmp")
    report_tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    report_tmp.replace(report_path)
    return {"sources_checked": len(new_state["sources"]), "new_observations": len(changed), "total_observations": len(all_rows), "discovery_candidates": len(new_state["discovery_candidates"])}
