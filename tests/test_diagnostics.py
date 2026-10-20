import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from ps5diagnostics.__main__ import dashboard_data
from ps5knowledge.db import build_database

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "research" / "knowledge-base" / "catalog.json"


class DiagnosticsTests(unittest.TestCase):
    def test_preapproval_dashboard_has_no_console_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "research.sqlite3"
            build_database(CATALOG, database)
            data = dashboard_data(database)
            self.assertIn("Not observed", data["connection"])
            self.assertIn("Unknown", data["firmware"])
            self.assertEqual(data["observations"], [])
            self.assertTrue(all("unverified" in service[1] for service in data["services"]))

    def test_approved_observations_survive_catalog_rebuild(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "research.sqlite3"
            build_database(CATALOG, database)
            with closing(sqlite3.connect(database)) as con:
                con.execute("INSERT INTO console_observation VALUES(?,?,?,?,?,?,?,?)", (
                    "example", "2026-10-20T12:00:00Z", "console-A", "firmware_version",
                    "example-version", "console-reported", "manual Settings UI", "https://www.playstation.com/en-ca/support/hardware/playstation-system-software-application-version/"
                ))
                con.commit()
            build_database(CATALOG, database)
            data = dashboard_data(database)
            self.assertEqual(data["firmware"], "example-version")
            self.assertEqual(len(data["observations"]), 1)


if __name__ == "__main__":
    unittest.main()
