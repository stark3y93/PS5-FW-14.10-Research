# Windows diagnostics dashboard (preapproval build)

From the repository root on Windows:

```powershell
$env:PYTHONPATH = 'src'
python -m ps5knowledge build-db
python -m ps5diagnostics
```

The native Tkinter window reads the local SQLite research database. It shows connection **not observed**, console-reported firmware **unknown**, Sony-documented methods marked **unverified**, and a table of separately approved observations. It contains no console discovery, socket, authentication or Remote Play automation code. The official PS Remote Play client would be used manually only after approval of the [separate plan](ps5-connection-diagnostics-approval-plan.md).

`console_observation` is an empty table in the existing SQLite database until an approved procedure records data. A catalog rebuild preserves existing local rows. The generated database is Git-ignored, so private device observations stay local. The research catalog and dashboard distinguish source documentation from actual console reports.

The dashboard's offline state and rebuild behavior are covered by `tests/test_diagnostics.py`. No live connection has been attempted.
