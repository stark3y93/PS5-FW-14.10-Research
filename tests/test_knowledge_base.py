import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from ps5knowledge.db import build_database, search, stats
from ps5knowledge.__main__ import dashboard_data, render_dashboard

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "research" / "knowledge-base" / "catalog.json"


class KnowledgeBaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "test.sqlite3"
        self.counts = build_database(CATALOG, self.db)

    def tearDown(self):
        self.temp.cleanup()

    def test_import_counts_and_source_links(self):
        self.assertEqual(self.counts["repositories"], 17)
        self.assertGreaterEqual(self.counts["sources"], 20)
        self.assertEqual(self.counts["findings"], 18)
        self.assertEqual(self.counts["sources"], 37)
        self.assertGreaterEqual(self.counts["evidence"], self.counts["findings"])
        with closing(sqlite3.connect(self.db)) as con:
            self.assertEqual(con.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertEqual(con.execute("SELECT count(*) FROM evidence WHERE source_url NOT LIKE 'https://%' AND source_url NOT LIKE '../../notes/%'").fetchone()[0], 0)
            self.assertGreater(con.execute("SELECT count(*) FROM commit_record").fetchone()[0], 0)
            self.assertGreater(con.execute("SELECT count(*) FROM vulnerability_source").fetchone()[0], 0)

    def test_search_finds_findings_and_questions(self):
        findings = search(self.db, "SLB2")
        self.assertTrue(any(x["kind"] == "finding" for x in findings))
        questions = search(self.db, "Sony build")
        self.assertTrue(any(x["kind"] == "question" for x in questions))

    def test_search_input_is_literal_and_limits_are_checked(self):
        self.assertEqual(search(self.db, '***!!!', 3), [])
        with self.assertRaises(ValueError):
            search(self.db, " ")
        with self.assertRaises(ValueError):
            search(self.db, "test", 101)

    def test_dashboard_has_metrics_and_clickable_evidence(self):
        data = dashboard_data(self.db)
        self.assertEqual(data["stats"]["repositories"], 17)
        page = render_dashboard(data)
        self.assertIn("Search findings", page)
        self.assertIn("https://", page)
        self.assertIn("Contradictions to review", page)
        self.assertIn("priority ", page)

    def test_catalog_references_resolve(self):
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        source_ids = {x["id"] for x in catalog["documents"]} | {x["id"] for x in catalog["repositories"]}
        finding_ids = {x["id"] for x in catalog["findings"]}
        component_ids = {x["id"] for x in catalog["components"]}
        firmware_ids = {x["id"] for x in catalog["firmware_versions"]}
        vuln_ids = {x["id"] for x in catalog["vulnerabilities"]}
        for finding in catalog["findings"]:
            self.assertTrue(finding["evidence"], finding["id"])
            for e in finding["evidence"]:
                self.assertIn(e["source_id"], source_ids)
            for key, known in (("component_ids", component_ids), ("vulnerability_ids", vuln_ids)):
                self.assertLessEqual(set(finding.get(key, [])), known)
            self.assertLessEqual({x["firmware_id"] for x in finding.get("firmware", [])}, firmware_ids)
        for contradiction in catalog["contradictions"]:
            self.assertLessEqual(set(contradiction["finding_ids"]), finding_ids)
            self.assertLessEqual(set(contradiction["source_ids"]), source_ids)
        for vulnerability in catalog["vulnerabilities"]:
            self.assertLessEqual(set(vulnerability["source_ids"]), source_ids)


if __name__ == "__main__":
    unittest.main()
