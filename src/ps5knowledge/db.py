"""Build and query a normalized SQLite knowledge base from catalog.json."""
from __future__ import annotations

import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE researcher(id TEXT PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL, url TEXT NOT NULL, attribution TEXT NOT NULL);
CREATE TABLE repository(id TEXT PRIMARY KEY, owner TEXT NOT NULL, name TEXT NOT NULL, url TEXT NOT NULL, commit_id TEXT NOT NULL, observed_head TEXT, license TEXT NOT NULL, contribution TEXT NOT NULL, coverage TEXT NOT NULL, summary TEXT NOT NULL, firmware_claim TEXT NOT NULL);
CREATE TABLE commit_record(id TEXT PRIMARY KEY, repository_id TEXT NOT NULL REFERENCES repository ON DELETE CASCADE, role TEXT NOT NULL, url TEXT NOT NULL);
CREATE TABLE repository_researcher(repository_id TEXT REFERENCES repository ON DELETE CASCADE, researcher_id TEXT REFERENCES researcher, PRIMARY KEY(repository_id,researcher_id));
CREATE TABLE source(id TEXT PRIMARY KEY, title TEXT NOT NULL, publisher TEXT NOT NULL, url TEXT NOT NULL, date TEXT, kind TEXT NOT NULL, provenance TEXT NOT NULL, summary TEXT NOT NULL);
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
CREATE TABLE contradiction(id TEXT PRIMARY KEY, title TEXT NOT NULL, status TEXT NOT NULL, severity TEXT NOT NULL, summary TEXT NOT NULL);
CREATE TABLE contradiction_finding(contradiction_id TEXT REFERENCES contradiction ON DELETE CASCADE, finding_id TEXT REFERENCES finding, PRIMARY KEY(contradiction_id,finding_id));
CREATE TABLE contradiction_source(contradiction_id TEXT REFERENCES contradiction ON DELETE CASCADE, source_id TEXT NOT NULL, PRIMARY KEY(contradiction_id,source_id));
CREATE VIRTUAL TABLE finding_fts USING fts5(finding_id UNINDEXED,title,summary,scope,firmware_relevance);
CREATE VIRTUAL TABLE question_fts USING fts5(question_id UNINDEXED,question,rationale,method);
CREATE INDEX evidence_finding_idx ON evidence(finding_id);
CREATE INDEX finding_firmware_idx ON finding_firmware(firmware_id);
"""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def build_database(catalog_path: str | Path, database_path: str | Path) -> dict[str, int]:
    """Rebuild a database atomically from the reviewable JSON source catalog."""
    catalog = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
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
        for row in catalog["repositories"]:
            con.execute("INSERT INTO repository VALUES(?,?,?,?,?,?,?,?,?,?,?)", (row["id"], row["owner"], row["name"], row["url"], row["commit"], row.get("observed_head"), row["license"], row["contribution"], row["coverage"], row["summary"], row["firmware_claim"]))
            con.execute("INSERT INTO commit_record VALUES(?,?,?,?)", (row["commit"], row["id"], "inspected", row["url"] + "/commit/" + row["commit"]))
            if row.get("observed_head") and row["observed_head"] != row["commit"]:
                con.execute("INSERT INTO commit_record VALUES(?,?,?,?)", (row["observed_head"], row["id"], "observed-head", row["url"] + "/commit/" + row["observed_head"]))
            con.executemany("INSERT INTO repository_researcher VALUES(?,?)", [(row["id"], x) for x in row.get("researchers", [])])
        for row in catalog["documents"]:
            con.execute("INSERT INTO source VALUES(?,?,?,?,?,?,?,?)", (row["id"], row["title"], row["publisher"], row["url"], row.get("date"), row["kind"], row["provenance"], row["summary"]))
            con.executemany("INSERT INTO source_researcher VALUES(?,?)", [(row["id"], x) for x in row.get("researchers", [])])
        for table, key, columns in (("component", "components", ("id", "name", "description")), ("firmware", "firmware_versions", ("id", "version", "build", "release_date", "status"))):
            for row in catalog[key]:
                con.execute(f"INSERT INTO {table} VALUES({','.join('?' for _ in columns)})", tuple(row.get(c) for c in columns))
        source_urls = {x["id"]: x["url"] for x in catalog["documents"]}
        source_urls.update({x["id"]: x["url"] for x in catalog["repositories"]})
        for row in catalog["vulnerabilities"]:
            con.execute("INSERT INTO vulnerability VALUES(?,?,?,?,?,?,?,?)", (row["id"], row["identifier"], row["title"], row["upstream_status"], row["upstream_summary"], _json(row["affected_products"]), row["mitigation"], row.get("disclosure_date")))
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
            con.execute("INSERT INTO finding_fts(finding_id,title,summary,scope,firmware_relevance) VALUES(?,?,?,?,?)", (row["id"], row["title"], row["summary"], row["scope"], row["firmware_relevance"]))
        for row in catalog["questions"]:
            con.execute("INSERT INTO question VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (row["id"], row["rank"], row["priority_score"], row["firmware_relevance_score"], row["question"], row["rationale"], row["evidence_quality_score"], row["answerability_score"], row["safe_verification_score"], row["community_value_score"], row["method"], row["stop_condition"]))
            con.execute("INSERT INTO question_fts(question_id,question,rationale,method) VALUES(?,?,?,?)", (row["id"], row["question"], row["rationale"], row["method"]))
        for row in catalog["contradictions"]:
            con.execute("INSERT INTO contradiction VALUES(?,?,?,?,?)", (row["id"], row["title"], row["status"], row["severity"], row["summary"]))
            con.executemany("INSERT INTO contradiction_finding VALUES(?,?)", [(row["id"], x) for x in row.get("finding_ids", [])])
            con.executemany("INSERT INTO contradiction_source VALUES(?,?)", [(row["id"], x) for x in row.get("source_ids", [])])
        con.commit()
        counts = {name: con.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for name, table in (("repositories", "repository"), ("documents", "source"), ("findings", "finding"), ("evidence", "evidence"), ("questions", "question"), ("contradictions", "contradiction"))}
        counts["sources"] = counts["repositories"] + counts["documents"]
        con.close()
        temp.replace(destination)
        return counts
    except Exception:
        con.close()
        temp.unlink(missing_ok=True)
        raise


def stats(database_path: str | Path) -> dict[str, int]:
    with closing(sqlite3.connect(database_path)) as con:
        counts = {name: con.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for name, table in (("repositories", "repository"), ("documents", "source"), ("findings", "finding"), ("evidence", "evidence"), ("questions", "question"), ("contradictions", "contradiction"))}
        counts["sources"] = counts["repositories"] + counts["documents"]
        counts["relevant_1410"] = con.execute("SELECT count(DISTINCT finding_id) FROM finding_firmware WHERE firmware_id='ps5-14.10'").fetchone()[0]
        counts["independently_verified"] = con.execute("SELECT count(*) FROM finding WHERE lower(reproduction_status) LIKE '%independent reproduction%' OR lower(reproduction_status) LIKE '%independently reproduced%'").fetchone()[0]
        counts["primary_source_checked"] = con.execute("SELECT count(*) FROM finding WHERE classification='VERIFIED'").fetchone()[0]
        counts["unverified_claims"] = con.execute("SELECT count(*) FROM finding WHERE classification IN ('AUTHOR-REPORTED','UNVERIFIED','HYPOTHESIS')").fetchone()[0]
        counts["firmware_versions"] = con.execute("SELECT count(*) FROM firmware").fetchone()[0]
    return counts


def search(database_path: str | Path, query: str, limit: int = 20) -> list[dict[str, str]]:
    """Search findings and open questions; quote user input as a literal FTS phrase."""
    if not query.strip() or not 1 <= limit <= 100:
        raise ValueError("query must be nonempty and limit must be 1..100")
    tokens = re.findall(r"[\w.-]+", query, flags=re.UNICODE)
    if not tokens:
        return []
    phrase = " AND ".join('"' + token.replace('"', '""') + '"' for token in tokens)
    results: list[dict[str, str]] = []
    with closing(sqlite3.connect(database_path)) as con:
        con.row_factory = sqlite3.Row
        for kind, table, id_col, title_col in (("finding", "finding_fts", "finding_id", "title"), ("question", "question_fts", "question_id", "question")):
            rows = con.execute(f"SELECT {id_col}, {title_col} FROM {table} WHERE {table} MATCH ? LIMIT ?", (phrase, limit)).fetchall()
            results.extend({"kind": kind, "id": row[0], "title": row[1]} for row in rows)
    return results[:limit]
