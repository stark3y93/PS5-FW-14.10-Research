"""Build and query a normalized SQLite knowledge base from catalog.json."""
from __future__ import annotations

import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from .ecosystem import canonical_repo, validate_compatibility_claim

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE researcher(id TEXT PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL, url TEXT NOT NULL, attribution TEXT NOT NULL);
CREATE TABLE repository(id TEXT PRIMARY KEY, owner TEXT NOT NULL, name TEXT NOT NULL, url TEXT NOT NULL, commit_id TEXT NOT NULL, observed_head TEXT, license TEXT NOT NULL, contribution TEXT NOT NULL, coverage TEXT NOT NULL, summary TEXT NOT NULL, firmware_claim TEXT NOT NULL);
CREATE TABLE commit_record(id TEXT PRIMARY KEY, repository_id TEXT NOT NULL REFERENCES repository ON DELETE CASCADE, role TEXT NOT NULL, url TEXT NOT NULL);
CREATE TABLE repository_researcher(repository_id TEXT REFERENCES repository ON DELETE CASCADE, researcher_id TEXT REFERENCES researcher, PRIMARY KEY(repository_id,researcher_id));
CREATE TABLE source(id TEXT PRIMARY KEY, title TEXT NOT NULL, publisher TEXT NOT NULL, url TEXT NOT NULL, date TEXT, kind TEXT NOT NULL, version_scope TEXT NOT NULL, provenance TEXT NOT NULL, summary TEXT NOT NULL);
CREATE TABLE source_researcher(source_id TEXT REFERENCES source ON DELETE CASCADE, researcher_id TEXT REFERENCES researcher, PRIMARY KEY(source_id,researcher_id));
CREATE TABLE component(id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL);
CREATE TABLE firmware(id TEXT PRIMARY KEY, version TEXT NOT NULL, build TEXT, release_date TEXT, status TEXT NOT NULL);
CREATE TABLE vulnerability(id TEXT PRIMARY KEY, identifier TEXT NOT NULL, title TEXT NOT NULL, upstream_status TEXT NOT NULL, upstream_summary TEXT NOT NULL, affected_products TEXT NOT NULL, mitigation TEXT NOT NULL, disclosure_date TEXT);
CREATE TABLE vulnerability_source(vulnerability_id TEXT REFERENCES vulnerability ON DELETE CASCADE, source_id TEXT NOT NULL, PRIMARY KEY(vulnerability_id,source_id));
CREATE TABLE finding(id TEXT PRIMARY KEY, title TEXT NOT NULL, classification TEXT NOT NULL, confidence TEXT NOT NULL, summary TEXT NOT NULL, scope TEXT NOT NULL, firmware_relevance TEXT NOT NULL, reproduction_status TEXT NOT NULL);
CREATE TABLE finding_component(finding_id TEXT REFERENCES finding ON DELETE CASCADE, component_id TEXT REFERENCES component, PRIMARY KEY(finding_id,component_id));
CREATE TABLE finding_researcher(finding_id TEXT REFERENCES finding ON DELETE CASCADE, researcher_id TEXT REFERENCES researcher, PRIMARY KEY(finding_id,researcher_id));
CREATE TABLE finding_vulnerability(finding_id TEXT REFERENCES finding ON DELETE CASCADE, vulnerability_id TEXT REFERENCES vulnerability, PRIMARY KEY(finding_id,vulnerability_id));
CREATE TABLE finding_firmware(finding_id TEXT REFERENCES finding ON DELETE CASCADE, firmware_id TEXT REFERENCES firmware, relationship TEXT NOT NULL, status TEXT NOT NULL, PRIMARY KEY(finding_id,firmware_id,relationship));
CREATE TABLE evidence(id INTEGER PRIMARY KEY, finding_id TEXT REFERENCES finding ON DELETE CASCADE, source_id TEXT NOT NULL, kind TEXT NOT NULL, locator TEXT NOT NULL, supports TEXT NOT NULL, source_url TEXT NOT NULL);
CREATE TABLE question(id TEXT PRIMARY KEY, rank INTEGER NOT NULL, priority_score REAL NOT NULL, firmware_relevance INTEGER NOT NULL, question TEXT NOT NULL, rationale TEXT NOT NULL, evidence_quality INTEGER NOT NULL, answerability INTEGER NOT NULL, safe_verification INTEGER NOT NULL, community_value INTEGER NOT NULL, method TEXT NOT NULL, stop_condition TEXT NOT NULL);
CREATE TABLE question_evidence(question_id TEXT REFERENCES question ON DELETE CASCADE, source_id TEXT NOT NULL, supports TEXT NOT NULL, source_url TEXT NOT NULL, PRIMARY KEY(question_id,source_id));
CREATE TABLE contradiction(id TEXT PRIMARY KEY, title TEXT NOT NULL, status TEXT NOT NULL, severity TEXT NOT NULL, summary TEXT NOT NULL);
CREATE TABLE contradiction_finding(contradiction_id TEXT REFERENCES contradiction ON DELETE CASCADE, finding_id TEXT REFERENCES finding, PRIMARY KEY(contradiction_id,finding_id));
CREATE TABLE contradiction_source(contradiction_id TEXT REFERENCES contradiction ON DELETE CASCADE, source_id TEXT NOT NULL, PRIMARY KEY(contradiction_id,source_id));
CREATE TABLE experiment(id TEXT PRIMARY KEY, title TEXT NOT NULL, status TEXT NOT NULL, confidence TEXT NOT NULL, method TEXT NOT NULL, result TEXT NOT NULL, firmware_relevance TEXT NOT NULL, source_url TEXT NOT NULL, log_path TEXT NOT NULL);
CREATE TABLE ecosystem_project(repository_id TEXT PRIMARY KEY REFERENCES repository ON DELETE CASCADE, categories TEXT NOT NULL, maturity TEXT NOT NULL, reuse_gate TEXT NOT NULL, checked_at TEXT NOT NULL, source_credibility TEXT NOT NULL);
CREATE TABLE compatibility_claim(id TEXT PRIMARY KEY, repository_id TEXT NOT NULL REFERENCES repository ON DELETE CASCADE, claim_type TEXT NOT NULL, component TEXT NOT NULL, firmware_scope TEXT NOT NULL, hardware_scope TEXT NOT NULL, evidence_class TEXT NOT NULL CHECK(evidence_class IN ('source_code','project_documentation','vendor_advisory','independent_test','third_party_report')), status TEXT NOT NULL CHECK(status IN ('author_reported','source_observed','independently_reproduced','unknown','contradicted')), source_url TEXT NOT NULL, pinned_commit TEXT NOT NULL, reproduction_record TEXT, notes TEXT NOT NULL);
CREATE TABLE platform_capability(id TEXT PRIMARY KEY, name TEXT NOT NULL, status TEXT NOT NULL, platform TEXT NOT NULL, firmware_scope TEXT NOT NULL, source_url TEXT NOT NULL, notes TEXT NOT NULL);
CREATE TABLE capability_project(capability_id TEXT REFERENCES platform_capability ON DELETE CASCADE, repository_id TEXT REFERENCES repository, PRIMARY KEY(capability_id,repository_id));
CREATE TABLE capability_dependency(capability_id TEXT REFERENCES platform_capability ON DELETE CASCADE, name TEXT NOT NULL, license TEXT NOT NULL, source_url TEXT NOT NULL, PRIMARY KEY(capability_id,name));
CREATE TABLE source_observation(id TEXT PRIMARY KEY, repository_id TEXT REFERENCES repository, repository_name TEXT NOT NULL, event_type TEXT NOT NULL, external_id TEXT NOT NULL, title TEXT NOT NULL, source_url TEXT NOT NULL, observed_at TEXT NOT NULL, upstream_updated_at TEXT, upstream_state TEXT, pinned_commit TEXT, license_at_review TEXT NOT NULL, classification TEXT NOT NULL CHECK(classification='UNVERIFIED_SOURCE_ACTIVITY'));
CREATE TABLE discovered_candidate(repository_name TEXT PRIMARY KEY, url TEXT NOT NULL, description TEXT NOT NULL, stars INTEGER NOT NULL, pushed_at TEXT, first_seen TEXT NOT NULL, status TEXT NOT NULL CHECK(status='candidate_unreviewed'));
CREATE VIRTUAL TABLE ecosystem_fts USING fts5(repository_id UNINDEXED,name,categories,maturity,reuse_gate,claim_text);
CREATE VIRTUAL TABLE finding_fts USING fts5(finding_id UNINDEXED,title,summary,scope,firmware_relevance,vulnerability_terms);
CREATE VIRTUAL TABLE question_fts USING fts5(question_id UNINDEXED,question,rationale,method);
CREATE VIRTUAL TABLE repository_fts USING fts5(repository_id UNINDEXED,owner,name,summary,firmware_claim,license);
CREATE VIRTUAL TABLE source_fts USING fts5(source_id UNINDEXED,title,publisher,summary,version_scope,provenance);
CREATE VIRTUAL TABLE researcher_fts USING fts5(researcher_id UNINDEXED,name,kind,attribution);
CREATE VIRTUAL TABLE vulnerability_fts USING fts5(vulnerability_id UNINDEXED,identifier,title,upstream_status,upstream_summary,affected_products);
CREATE INDEX evidence_finding_idx ON evidence(finding_id);
CREATE INDEX finding_firmware_idx ON finding_firmware(firmware_id);
"""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def build_database(catalog_path: str | Path, database_path: str | Path, ecosystem_path: str | Path | None = None, updates_path: str | Path | None = None) -> dict[str, int]:
    """Rebuild a database atomically from the reviewable JSON source catalog."""
    catalog = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
    ecosystem_path = Path(ecosystem_path) if ecosystem_path else Path(catalog_path).with_name("ecosystem.json")
    ecosystem = json.loads(ecosystem_path.read_text(encoding="utf-8")) if ecosystem_path.exists() else {"repositories": [], "projects": [], "compatibility_claims": [], "capabilities": []}
    updates_path = Path(updates_path) if updates_path else Path(catalog_path).with_name("updates.json")
    updates = json.loads(updates_path.read_text(encoding="utf-8")) if updates_path.exists() else {"observations": [], "discovery_candidates": []}
    destination = Path(database_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_suffix(destination.suffix + ".tmp")
    if temp.exists():
        temp.unlink()
    con = sqlite3.connect(temp)
    try:
        con.executescript(SCHEMA)
        for row in catalog["researchers"]:
            con.execute("INSERT INTO researcher VALUES(?,?,?,?,?)", (row["id"], row["name"], row["kind"], row["url"], row["attribution"]))
            con.execute("INSERT INTO researcher_fts VALUES(?,?,?,?)", (row["id"], row["name"], row["kind"], row["attribution"]))
        for row in catalog["repositories"]:
            con.execute("INSERT INTO repository VALUES(?,?,?,?,?,?,?,?,?,?,?)", (row["id"], row["owner"], row["name"], row["url"], row["commit"], row.get("observed_head"), row["license"], row["contribution"], row["coverage"], row["summary"], row["firmware_claim"]))
            con.execute("INSERT INTO repository_fts VALUES(?,?,?,?,?,?)", (row["id"], row["owner"], row["name"], row["summary"], row["firmware_claim"], row["license"]))
            con.execute("INSERT INTO commit_record VALUES(?,?,?,?)", (row["commit"], row["id"], "inspected", row["url"] + "/commit/" + row["commit"]))
            if row.get("observed_head") and row["observed_head"] != row["commit"]:
                con.execute("INSERT INTO commit_record VALUES(?,?,?,?)", (row["observed_head"], row["id"], "observed-head", row["url"] + "/commit/" + row["observed_head"]))
            con.executemany("INSERT INTO repository_researcher VALUES(?,?)", [(row["id"], x) for x in row.get("researchers", [])])
        known_repo_ids = {row["id"] for row in catalog["repositories"]}
        known_repo_urls = {canonical_repo(row["url"]): row["id"] for row in catalog["repositories"]}
        for row in ecosystem.get("repositories", []):
            normalized = canonical_repo(row["url"])
            if row["id"] in known_repo_ids or normalized in known_repo_urls:
                raise ValueError(f"duplicate ecosystem repository identity: {row['id']} / {row['url']}")
            con.execute("INSERT INTO repository VALUES(?,?,?,?,?,?,?,?,?,?,?)", (row["id"], row["owner"], row["name"], row["url"], row["commit"], row.get("observed_head"), row["license"], row["contribution"], row["coverage"], row["summary"], row["firmware_claim"]))
            con.execute("INSERT INTO repository_fts VALUES(?,?,?,?,?,?)", (row["id"], row["owner"], row["name"], row["summary"], row["firmware_claim"], row["license"]))
            con.execute("INSERT INTO commit_record VALUES(?,?,?,?)", (row["commit"], row["id"], "inspected", row["url"] + "/commit/" + row["commit"]))
            known_repo_ids.add(row["id"])
            known_repo_urls[normalized] = row["id"]
        for row in catalog["documents"]:
            con.execute("INSERT INTO source VALUES(?,?,?,?,?,?,?,?,?)", (row["id"], row["title"], row["publisher"], row["url"], row.get("date"), row["kind"], row["version_scope"], row["provenance"], row["summary"]))
            con.execute("INSERT INTO source_fts VALUES(?,?,?,?,?,?)", (row["id"], row["title"], row["publisher"], row["summary"], row["version_scope"], row["provenance"]))
            con.executemany("INSERT INTO source_researcher VALUES(?,?)", [(row["id"], x) for x in row.get("researchers", [])])
        for table, key, columns in (("component", "components", ("id", "name", "description")), ("firmware", "firmware_versions", ("id", "version", "build", "release_date", "status"))):
            for row in catalog[key]:
                con.execute(f"INSERT INTO {table} VALUES({','.join('?' for _ in columns)})", tuple(row.get(c) for c in columns))
        source_urls = {x["id"]: x["url"] for x in catalog["documents"]}
        source_urls.update({x["id"]: x["url"] + "/tree/" + x["commit"] for x in catalog["repositories"]})
        for row in catalog["vulnerabilities"]:
            con.execute("INSERT INTO vulnerability VALUES(?,?,?,?,?,?,?,?)", (row["id"], row["identifier"], row["title"], row["upstream_status"], row["upstream_summary"], _json(row["affected_products"]), row["mitigation"], row.get("disclosure_date")))
            con.execute("INSERT INTO vulnerability_fts VALUES(?,?,?,?,?,?)", (row["id"], row["identifier"], row["title"], row["upstream_status"], row["upstream_summary"], " ".join(row["affected_products"])))
            unknown = set(row.get("source_ids", [])) - source_urls.keys()
            if unknown:
                raise ValueError(f"unknown vulnerability source(s) {sorted(unknown)} in {row['id']}")
            con.executemany("INSERT INTO vulnerability_source VALUES(?,?)", [(row["id"], x) for x in row.get("source_ids", [])])
        for row in catalog["findings"]:
            con.execute("INSERT INTO finding VALUES(?,?,?,?,?,?,?,?)", tuple(row[k] for k in ("id", "title", "classification", "confidence", "summary", "scope", "firmware_relevance", "reproduction_status")))
            for table, field, col in (("finding_component", "component_ids", "component_id"), ("finding_researcher", "researcher_ids", "researcher_id"), ("finding_vulnerability", "vulnerability_ids", "vulnerability_id")):
                con.executemany(f"INSERT INTO {table}(finding_id,{col}) VALUES(?,?)", [(row["id"], x) for x in row.get(field, [])])
            con.executemany("INSERT INTO finding_firmware VALUES(?,?,?,?)", [(row["id"], x["firmware_id"], x["relationship"], x["status"]) for x in row.get("firmware", [])])
            for e in row.get("evidence", []):
                if e["source_id"] not in source_urls:
                    raise ValueError(f"unknown evidence source {e['source_id']} in {row['id']}")
                con.execute("INSERT INTO evidence(finding_id,source_id,kind,locator,supports,source_url) VALUES(?,?,?,?,?,?)", (row["id"], e["source_id"], e["kind"], e["locator"], e["supports"], source_urls[e["source_id"]]))
            vuln_terms = " ".join(v["identifier"] + " " + v["title"] for v in catalog["vulnerabilities"] if v["id"] in row.get("vulnerability_ids", []))
            con.execute("INSERT INTO finding_fts(finding_id,title,summary,scope,firmware_relevance,vulnerability_terms) VALUES(?,?,?,?,?,?)", (row["id"], row["title"], row["summary"], row["scope"], row["firmware_relevance"], vuln_terms))
        for row in catalog["questions"]:
            con.execute("INSERT INTO question VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (row["id"], row["rank"], row["priority_score"], row["firmware_relevance_score"], row["question"], row["rationale"], row["evidence_quality_score"], row["answerability_score"], row["safe_verification_score"], row["community_value_score"], row["method"], row["stop_condition"]))
            unknown = {e["source_id"] for e in row.get("evidence", [])} - source_urls.keys()
            if unknown:
                raise ValueError(f"unknown question source(s) {sorted(unknown)} in {row['id']}")
            con.executemany("INSERT INTO question_evidence VALUES(?,?,?,?)", [(row["id"], e["source_id"], e["supports"], source_urls[e["source_id"]]) for e in row.get("evidence", [])])
            con.execute("INSERT INTO question_fts(question_id,question,rationale,method) VALUES(?,?,?,?)", (row["id"], row["question"], row["rationale"], row["method"]))
        for row in catalog["contradictions"]:
            con.execute("INSERT INTO contradiction VALUES(?,?,?,?,?)", (row["id"], row["title"], row["status"], row["severity"], row["summary"]))
            con.executemany("INSERT INTO contradiction_finding VALUES(?,?)", [(row["id"], x) for x in row.get("finding_ids", [])])
            con.executemany("INSERT INTO contradiction_source VALUES(?,?)", [(row["id"], x) for x in row.get("source_ids", [])])
        for row in catalog.get("experiments", []):
            con.execute("INSERT INTO experiment VALUES(?,?,?,?,?,?,?,?,?)", tuple(row[k] for k in ("id", "title", "status", "confidence", "method", "result", "firmware_relevance", "source_url", "log_path")))
        for row in ecosystem.get("projects", []):
            if row["repository_id"] not in known_repo_ids:
                raise ValueError(f"unknown ecosystem repository {row['repository_id']}")
            con.execute("INSERT INTO ecosystem_project VALUES(?,?,?,?,?,?)", (row["repository_id"], _json(row["categories"]), row["maturity"], row["reuse_gate"], row.get("checked_at", ecosystem.get("snapshot_date", "unknown")), row.get("source_credibility", "pinned primary project source; technical claims remain author reported unless independently reproduced")))
        for row in ecosystem.get("compatibility_claims", []):
            validate_compatibility_claim(row)
            if row["repository_id"] not in known_repo_ids:
                raise ValueError(f"unknown compatibility repository {row['repository_id']}")
            con.execute("INSERT INTO compatibility_claim VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", tuple(row.get(k) for k in ("id", "repository_id", "claim_type", "component", "firmware_scope", "hardware_scope", "evidence_class", "status", "source_url", "pinned_commit", "reproduction_record", "notes")))
            con.execute("INSERT INTO ecosystem_fts VALUES(?,?,?,?,?,?)", (row["repository_id"], row["repository_id"], row["claim_type"] + " " + row["component"], row["status"], row["source_url"], row["firmware_scope"] + " " + row["notes"]))
        for project in ecosystem.get("projects", []):
            repo = con.execute("SELECT name FROM repository WHERE id=?", (project["repository_id"],)).fetchone()
            claims = " ".join(x["firmware_scope"] + " " + x["notes"] for x in ecosystem.get("compatibility_claims", []) if x["repository_id"] == project["repository_id"])
            con.execute("INSERT INTO ecosystem_fts VALUES(?,?,?,?,?,?)", (project["repository_id"], repo[0], " ".join(project["categories"]), project["maturity"], project["reuse_gate"], claims))
        for row in ecosystem.get("capabilities", []):
            con.execute("INSERT INTO platform_capability VALUES(?,?,?,?,?,?,?)", (row["id"], row["name"], row["status"], row["platform"], row["firmware_scope"], row["source_url"], row["notes"]))
            unknown = set(row["projects"]) - known_repo_ids
            if unknown:
                raise ValueError(f"unknown project(s) in capability {row['id']}: {sorted(unknown)}")
            con.executemany("INSERT INTO capability_project VALUES(?,?)", [(row["id"], x) for x in row["projects"]])
            con.executemany("INSERT INTO capability_dependency VALUES(?,?,?,?)", [(row["id"], x["name"], x["license"], x["source_url"]) for x in row["dependencies"]])
        for row in updates.get("observations", []):
            repo_id = row.get("repository_id")
            if repo_id and repo_id not in known_repo_ids:
                raise ValueError(f"unknown observed repository {repo_id}")
            con.execute("INSERT INTO source_observation VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (row["id"], repo_id, row["repository"], row["event_type"], str(row["external_id"]), row["title"], row["source_url"], row["observed_at"], row.get("upstream_updated_at"), row.get("upstream_state"), row.get("pinned_commit"), row.get("license_at_review", "unknown"), "UNVERIFIED_SOURCE_ACTIVITY"))
        for row in updates.get("discovery_candidates", []):
            con.execute("INSERT INTO discovered_candidate VALUES(?,?,?,?,?,?,?)", (row["repository_name"], row["url"], row.get("description") or "", int(row.get("stars") or 0), row.get("pushed_at"), row["first_seen"], "candidate_unreviewed"))
        con.commit()
        counts = {name: con.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for name, table in (("repositories", "repository"), ("documents", "source"), ("findings", "finding"), ("evidence", "evidence"), ("questions", "question"), ("question_evidence", "question_evidence"), ("contradictions", "contradiction"))}
        counts["sources"] = counts["repositories"] + counts["documents"]
        counts["experiments"] = con.execute("SELECT count(*) FROM experiment").fetchone()[0]
        counts["ecosystem_projects"] = con.execute("SELECT count(*) FROM ecosystem_project").fetchone()[0]
        counts["compatibility_claims"] = con.execute("SELECT count(*) FROM compatibility_claim").fetchone()[0]
        counts["platform_capabilities"] = con.execute("SELECT count(*) FROM platform_capability").fetchone()[0]
        counts["source_observations"] = con.execute("SELECT count(*) FROM source_observation").fetchone()[0]
        counts["discovery_candidates"] = con.execute("SELECT count(*) FROM discovered_candidate").fetchone()[0]
        con.close()
        temp.replace(destination)
        return counts
    except Exception:
        con.close()
        temp.unlink(missing_ok=True)
        raise


def stats(database_path: str | Path) -> dict[str, int]:
    with closing(sqlite3.connect(database_path)) as con:
        counts = {name: con.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for name, table in (("repositories", "repository"), ("documents", "source"), ("findings", "finding"), ("evidence", "evidence"), ("questions", "question"), ("question_evidence", "question_evidence"), ("contradictions", "contradiction"))}
        counts["sources"] = counts["repositories"] + counts["documents"]
        counts["experiments"] = con.execute("SELECT count(*) FROM experiment").fetchone()[0]
        counts["relevant_1410"] = con.execute("SELECT count(DISTINCT finding_id) FROM finding_firmware WHERE firmware_id='ps5-14.10'").fetchone()[0]
        counts["independently_verified"] = con.execute("SELECT count(*) FROM finding WHERE lower(reproduction_status) LIKE '%independent reproduction%' OR lower(reproduction_status) LIKE '%independently reproduced%'").fetchone()[0]
        counts["primary_source_checked"] = con.execute("SELECT count(*) FROM finding WHERE classification='VERIFIED'").fetchone()[0]
        counts["unverified_claims"] = con.execute("SELECT count(*) FROM finding WHERE classification IN ('AUTHOR-REPORTED','UNVERIFIED','HYPOTHESIS')").fetchone()[0]
        counts["firmware_versions"] = con.execute("SELECT count(*) FROM firmware").fetchone()[0]
        counts["compatibility_claims"] = con.execute("SELECT count(*) FROM compatibility_claim").fetchone()[0]
        counts["ecosystem_projects"] = con.execute("SELECT count(*) FROM ecosystem_project").fetchone()[0]
        counts["platform_capabilities"] = con.execute("SELECT count(*) FROM platform_capability").fetchone()[0]
        counts["source_observations"] = con.execute("SELECT count(*) FROM source_observation").fetchone()[0]
        counts["discovery_candidates"] = con.execute("SELECT count(*) FROM discovered_candidate").fetchone()[0]
    return counts


def search(database_path: str | Path, query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Search all knowledge entities; quote tokens so user input is literal FTS text."""
    if not query.strip() or not 1 <= limit <= 100:
        raise ValueError("query must be nonempty and limit must be 1..100")
    tokens = re.findall(r"[\w.-]+", query, flags=re.UNICODE)
    if not tokens:
        return []
    phrase = " AND ".join('"' + token.replace('"', '""') + '"' for token in tokens)
    groups: list[list[dict[str, Any]]] = []
    with closing(sqlite3.connect(database_path)) as con:
        con.row_factory = sqlite3.Row
        specs = (("finding", "finding_fts", "finding_id", "title"), ("question", "question_fts", "question_id", "question"), ("repository", "repository_fts", "repository_id", "name"), ("ecosystem_project", "ecosystem_fts", "repository_id", "name"), ("source", "source_fts", "source_id", "title"), ("vulnerability", "vulnerability_fts", "vulnerability_id", "title"), ("researcher", "researcher_fts", "researcher_id", "name"))
        for kind, table, id_col, title_col in specs:
            group = []
            query_sql = f"SELECT {id_col}, {title_col} FROM {table} WHERE {table} MATCH ? LIMIT ?"
            if kind == "ecosystem_project":
                query_sql = f"SELECT {id_col}, min({title_col}) FROM {table} WHERE {table} MATCH ? GROUP BY {id_col} LIMIT ?"
            for row in con.execute(query_sql, (phrase, limit)):
                item = {"kind": kind, "id": row[0], "title": row[1], "evidence": []}
                if kind == "finding":
                    refs = con.execute("SELECT source_id,source_url FROM evidence WHERE finding_id=?", (row[0],))
                elif kind == "question":
                    refs = con.execute("SELECT source_id,source_url FROM question_evidence WHERE question_id=?", (row[0],))
                elif kind == "repository":
                    refs = con.execute("SELECT ? AS source_id,url AS source_url FROM commit_record WHERE repository_id=? AND role='inspected'", (row[0], row[0]))
                elif kind == "ecosystem_project":
                    refs = con.execute("SELECT repository_id AS source_id,source_url FROM compatibility_claim WHERE repository_id=? UNION SELECT id,url FROM repository WHERE id=?", (row[0], row[0]))
                elif kind == "source":
                    refs = con.execute("SELECT id AS source_id,url AS source_url FROM source WHERE id=?", (row[0],))
                elif kind == "vulnerability":
                    refs = con.execute("SELECT vs.source_id, COALESCE(s.url,r.url) AS source_url FROM vulnerability_source vs LEFT JOIN source s ON s.id=vs.source_id LEFT JOIN repository r ON r.id=vs.source_id WHERE vs.vulnerability_id=?", (row[0],))
                else:
                    refs = con.execute("SELECT id AS source_id,url AS source_url FROM researcher WHERE id=?", (row[0],))
                item["evidence"] = [{"source_id": e[0], "url": e[1]} for e in refs]
                group.append(item)
            groups.append(group)
    results = []
    for index in range(max((len(g) for g in groups), default=0)):
        for group in groups:
            if index < len(group):
                results.append(group[index])
                if len(results) == limit:
                    return results
    return results
