# Synthetic browser records

These are fabricated test inputs, **not PS5 results**. They deliberately disagree about FontFace to demonstrate the importer. A JSON record can be edited by anyone; the importer never authenticates a console or firmware and never verifies a vulnerability.

```powershell
Set-Location E:\PS5-FW-14.10-Research
python -S tools/ps5_research.py --browser-diagnostic research/examples/browser/synthetic-complete.json research/examples/browser/synthetic-conflict.json --format markdown
python -S tools/ps5_research.py --browser-diagnostic research/examples/browser/synthetic-complete.json research/examples/browser/synthetic-conflict.json --format json
```

The output contains one observation conflict and unproven privileged boundaries. JSON pointers refer to values in the exact SHA-256 hashed input file; no input file is rewritten. The complete schema accepts the 15 named features in `browser_evidence.py`, Boolean values or `"error"`, and a self-reported `N.NN` firmware label. The timestamp is deliberately unvalidated as evidence of time. File size is capped at 64 KiB, nesting at 12, and inputs at 64 files. Unknown extra fields are flagged and ignored as unsupported claims. `started`/`error` captures are retained as incomplete and excluded from comparisons. Missing features are unknown. Only matching-label, complete, nonduplicate records with a consistent PS5-looking UA are compared. A PS5-looking UA still does not authenticate the target.
