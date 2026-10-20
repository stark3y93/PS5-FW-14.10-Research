import json
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from ps5knowledge.db import build_database, search
from ps5knowledge.ecosystem import (
    UNVERIFIED,
    canonical_repo,
    deduplicate_projects,
    merge_observations,
    observation_id,
    poll_sources,
    update_files,
    validate_compatibility_claim,
)

ROOT = Path(__file__).resolve().parents[1]
ECOSYSTEM = ROOT / "research" / "knowledge-base" / "ecosystem.json"
CATALOG = ROOT / "research" / "knowledge-base" / "catalog.json"


class EcosystemModelTests(unittest.TestCase):
    def test_canonical_repository_deduplicates_url_spellings(self):
        self.assertEqual(canonical_repo("https://github.com/PS5Dev/PS5SDK.git/"), "ps5dev/ps5sdk")
        with self.assertRaises(ValueError):
            canonical_repo("https://example.com/not-github")

    def test_duplicate_projects_merge_categories_and_keep_stable_identity(self):
        rows = [
            {"id": "ps5-linux", "url": "https://github.com/PS5Dev/PS5-Linux", "commit": "abc", "license": "GPL-3.0", "categories": ["linux"]},
            {"id": "linux-alias", "url": "ps5dev/ps5-linux", "commit": "abc", "license": "GPL-3.0", "categories": ["graphics"]},
        ]
        merged = deduplicate_projects(rows)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["id"], "ps5-linux")
        self.assertEqual(merged[0]["categories"], ["graphics", "linux"])

    def test_duplicate_project_rejects_commit_or_license_conflict(self):
        rows = [{"id": "a", "url": "x/y", "commit": "one", "license": "MIT"}, {"id": "b", "url": "X/Y", "commit": "two", "license": "MIT"}]
        with self.assertRaisesRegex(ValueError, "conflicting commit"):
            deduplicate_projects(rows)

    def test_firmware_claim_requires_version_scope_and_pinned_evidence(self):
        claim = {"evidence_class": "project_documentation", "status": "author_reported", "source_url": "https://github.com/example/project", "pinned_commit": "abc", "firmware_scope": "unknown"}
        validate_compatibility_claim(claim)
        claim["firmware_scope"] = ""
        with self.assertRaisesRegex(ValueError, "explicit firmware range"):
            validate_compatibility_claim(claim)

    def test_claim_cannot_be_promoted_to_verified_without_reproduction(self):
        claim = {"evidence_class": "project_documentation", "status": "independently_reproduced", "source_url": "https://github.com/example/project", "pinned_commit": "abc", "firmware_scope": "14.10"}
        with self.assertRaisesRegex(ValueError, "requires independent_test"):
            validate_compatibility_claim(claim)
        claim["evidence_class"] = "independent_test"
        with self.assertRaisesRegex(ValueError, "reproduction record"):
            validate_compatibility_claim(claim)
        claim["reproduction_record"] = "test report id"
        validate_compatibility_claim(claim)

    def test_unrecognized_claim_status_is_rejected(self):
        claim = {"evidence_class": "source_code", "status": "verified", "source_url": "https://github.com/example/project", "pinned_commit": "abc", "firmware_scope": "not stated"}
        with self.assertRaisesRegex(ValueError, "unsupported evidence status"):
            validate_compatibility_claim(claim)


class IncrementalSourceTrackingTests(unittest.TestCase):
    def fake_api(self, url, token=None):
        if "/search/repositories?" in url:
            return 200, {"items": [
                {"full_name": "NewOrg/NewPS5", "html_url": "https://github.com/NewOrg/NewPS5", "description": "candidate", "stargazers_count": 3, "pushed_at": "2026-10-19T00:00:00Z"},
                {"full_name": "Example/Tracked", "html_url": "https://github.com/Example/Tracked", "description": "tracked", "stargazers_count": 20, "pushed_at": "2026-10-20T00:00:00Z"},
            ]}, {}
        if url.endswith("/commits/main"):
            return 200, {"sha": "head-1"}, {}
        if "/commits?" in url:
            return 200, [{"sha": "commit-1", "commit": {"message": "source update\nbody", "committer": {"date": "2026-10-20T10:00:00Z"}}, "html_url": "https://github.com/Example/Tracked/commit/commit-1"}], {}
        if "/releases?" in url:
            return 200, [{"id": 12, "tag_name": "v1.0", "name": "release one", "html_url": "https://github.com/Example/Tracked/releases/tag/v1.0", "published_at": "2026-10-20T09:00:00Z"}], {}
        if "/issues?" in url:
            return 200, [
                {"id": 4, "title": "issue update", "state": "closed", "html_url": "https://github.com/Example/Tracked/issues/2", "updated_at": "2026-10-20T10:00:00Z"},
                {"id": 5, "title": "pull update", "state": "open", "html_url": "https://github.com/Example/Tracked/pull/3", "updated_at": "2026-10-20T10:01:00Z", "pull_request": {"url": "api"}},
            ], {}
        if url.endswith("/repos/example/tracked"):
            return 200, {"default_branch": "main", "pushed_at": "2026-10-20T10:00:00Z", "license": {"spdx_id": "MIT"}}, {}
        raise AssertionError(f"unexpected API request: {url}")

    def test_incremental_poll_tracks_commit_release_issue_and_pull_request(self):
        requests = []
        def api(url, token=None):
            requests.append(url)
            return self.fake_api(url, token)
        config = {"enabled": True, "baseline_date": "2026-10-20", "discovery_queries": ["PS5 homebrew"], "projects": [
            {"id": "tracked", "url": "https://github.com/Example/Tracked", "commit": "base", "license": "MIT"}
        ]}
        state, events = poll_sources(config, now="2026-10-20T12:00:00Z", request_json=api)
        self.assertEqual({x["event_type"] for x in events}, {"commit", "release", "issue", "pull_request"})
        self.assertTrue(all(x["classification"] == UNVERIFIED for x in events))
        self.assertEqual({x.get("upstream_state") for x in events if x["event_type"] in {"issue", "pull_request"}}, {"open", "closed"})
        self.assertIn("last_checked", state["sources"]["example/tracked"])
        self.assertTrue(any("since=2026-10-19" in url for url in requests))
        self.assertEqual([x["repository_name"] for x in state["discovery_candidates"]], ["neworg/newps5"])

    def test_observation_merge_deduplicates_and_preserves_first_source_pin(self):
        old = {"id": observation_id("Org/Repo", "commit", "sha1"), "repository": "Org/Repo", "repository_id": "r", "event_type": "commit", "external_id": "sha1", "title": "old", "source_url": "https://github.com/Org/Repo/commit/sha1", "observed_at": "2026-10-20T10:00:00Z", "first_seen": "2026-10-20T10:00:00Z", "pinned_commit": "sha1", "classification": UNVERIFIED}
        updated = dict(old, title="refreshed", source_url="https://different.invalid", observed_at="2026-10-20T12:00:00Z", classification="VERIFIED", pinned_commit="sha2")
        merged = merge_observations([old], [updated])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["title"], "refreshed")
        self.assertEqual(merged[0]["source_url"], old["source_url"])
        self.assertEqual(merged[0]["first_seen"], old["first_seen"])
        self.assertEqual(merged[0]["pinned_commit"], "sha1")
        self.assertEqual(merged[0]["classification"], UNVERIFIED)

    def test_disabled_update_job_does_not_access_network_or_write_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "updates.json"
            report = Path(tmp) / "report.md"
            result = update_files(ECOSYSTEM, state, report)
            self.assertEqual(result["skipped_disabled"], 1)
            self.assertFalse(state.exists())
            self.assertFalse(report.exists())

    def test_database_ingests_observations_as_unverified_source_activity(self):
        with tempfile.TemporaryDirectory() as tmp:
            update_path = Path(tmp) / "updates.json"
            event = {"repository": "ps5-linux/ps5-linux-loader", "repository_id": "r-ps5-linux-loader", "event_type": "release", "external_id": "r1", "title": "tag", "source_url": "https://github.com/ps5-linux/ps5-linux-loader/releases/tag/r1", "observed_at": "2026-10-20T12:00:00Z", "upstream_updated_at": "2026-10-20T11:00:00Z", "pinned_commit": "62020f57356375acb713ca5bfc3749c0fb209546", "license_at_review": "GPL-3.0", "classification": "AUTHOR-REPORTED", "id": observation_id("ps5-linux/ps5-linux-loader", "release", "r1")}
            update_path.write_text(json.dumps({"observations": [event], "discovery_candidates": []}), encoding="utf-8")
            db = Path(tmp) / "kb.sqlite3"
            counts = build_database(CATALOG, db, ECOSYSTEM, update_path)
            self.assertEqual(counts["source_observations"], 1)
            import sqlite3
            with closing(sqlite3.connect(db)) as con:
                stored = con.execute("SELECT classification,upstream_state FROM source_observation WHERE id=?", (event["id"],)).fetchone()
            self.assertEqual(stored, (UNVERIFIED, None))
            self.assertTrue(any(x["kind"] == "ecosystem_project" for x in search(db, "ps5-linux-loader")))
            self.assertTrue(any(x["kind"] == "ecosystem_project" for x in search(db, "RADV conformance")))

    def test_catalog_has_no_independently_reproduced_compatibility_claim_for_1410(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "kb.sqlite3"
            build_database(CATALOG, db, ECOSYSTEM)
            import sqlite3
            with closing(sqlite3.connect(db)) as con:
                self.assertEqual(con.execute("SELECT count(*) FROM compatibility_claim WHERE firmware_scope LIKE '%14.10%' AND status='independently_reproduced'").fetchone()[0], 0)
                self.assertEqual(con.execute("SELECT status FROM compatibility_claim WHERE id='cc-no-1410-linux'").fetchone()[0], "unknown")
                self.assertEqual(con.execute("SELECT status FROM compatibility_claim WHERE id='cc-1410-author-projects'").fetchone()[0], "author_reported")

    def test_database_rejects_duplicate_repo_urls_across_catalogs(self):
        with tempfile.TemporaryDirectory() as tmp:
            ecosystem = json.loads(ECOSYSTEM.read_text(encoding="utf-8"))
            duplicate = dict(ecosystem["repositories"][0])
            duplicate["id"] = "duplicate-alias"
            duplicate["url"] = duplicate["url"].replace("ps5-linux", "PS5-LINUX") + ".git"
            ecosystem["repositories"].append(duplicate)
            ecosystem_path = Path(tmp) / "ecosystem.json"
            ecosystem_path.write_text(json.dumps(ecosystem), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate ecosystem repository"):
                build_database(CATALOG, Path(tmp) / "bad.sqlite3", ecosystem_path)


if __name__ == "__main__":
    unittest.main()
