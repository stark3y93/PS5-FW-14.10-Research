# PS5 research knowledge base

This is a source-linked index of public PS5 research and upstream technical evidence, with the project's existing SLB2 observations kept separate from third-party claims. The reviewable seed is [`catalog.json`](catalog.json). It contains no Sony firmware, extracted data, keys, or binary payloads. Public projects are pinned to inspected Git commit IDs; license status is recorded per repository, and absent licenses are not treated as permission to reuse code.

## Current snapshot

Snapshot date: 2026-10-20. The seed has **37 indexed source records** (17 repositories and 20 technical/vendor documents), **18 deduplicated findings**, **29 finding-to-evidence links**, **10 firmware-version records**, **9 vulnerability records**, **11 components**, **8 ranked questions**, and **3 unresolved contradictions**. All 18 findings have an explicit 14.10 relevance row; that includes findings whose status is explicitly unknown or only author-reported.

Eleven findings are marked `VERIFIED` in the catalog, meaning the bounded statement is checked against its cited primary source, source code, or reproducible local measurement as described in `reproduction_status`. This does **not** mean a PS5 vulnerability was independently reproduced. The strict dashboard metric “independently verified” is **zero**: no vulnerability claim in this dataset has been independently reproduced on a device, and no device tests were performed. Seven findings remain author-reported. See [`catalog.json`](catalog.json) for claim scope and confidence per row.

The previous active PR #13 source index covered 7 repositories and 18 classified evidence links. This consolidated catalog preserves those pinned references and normalizes the earlier source-review material, adds 10 additional repository records relative to that PR baseline, and adds 20 first-class document/source records. “New” here means newly represented as searchable structured records; it does not imply new vulnerability discovery. Several records consolidate prior project notes, so do not sum every record as new technical knowledge.

Coverage labels intentionally differentiate README/scope extraction from source-level review. Most exploit and payload repositories were **not executed**. Repository identity and license are pinned to the inspected tree; a matching public default-branch head was observed at catalog time where recorded. A commit hash verifies a source snapshot identity, not the correctness of its claims.

## Build and search

Python 3.10+ with SQLite FTS5 is required; there are no additional runtime packages.

From the repository root in PowerShell:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -S -m ps5knowledge build-db
python -S -m ps5knowledge stats
python -S -m ps5knowledge search 'WebKit Sony'
python -S -m ps5knowledge dashboard
```

The default outputs are local `ps5-research.sqlite3` and `dashboard.html` files in this directory. They are reproducibly generated from `catalog.json` and ignored by Git so the human-reviewable JSON stays the source of truth. Use `--catalog`, `--database`, and `--output` to select different paths. Search is local FTS5; terms are treated as literal quoted tokens, not SQL or FTS query syntax. The static dashboard can be opened in a browser without a server or external JavaScript dependencies.

Run the firmware-free project suite from a clean checkout:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -S -m unittest discover -s tests -v
```

The knowledge-base tests build a temporary database from the JSON seed, check cross-references and evidence URLs, exercise search and render the dashboard. They do not access the 14.10 package, a console, or the network.

## Data model and evidence rules

SQLite normalizes repositories, inspected commits, researchers, source documents, firmware versions, components, vulnerabilities, findings, evidence links, questions and contradictions. FTS5 indexes finding statements and open questions. The `evidence` relation preserves each citation and the exact assertion it supports, including multiple citations for a deduplicated finding.

Use these distinctions when reading results:

- `VERIFIED`: only the bounded statement in the summary is supported by the cited source/reproducible measurement. Read the scope and reproduction fields.
- `AUTHOR-REPORTED`: a pinned author states the finding; this project did not independently reproduce it.
- `unknown` / `unresolved`: no conclusion. Missing support is not evidence of a patch or vulnerability.
- upstream FreeBSD, Apple, WebKitGTK, or WebKit advisories establish facts for those upstream/vendor products only. Sony component/build mapping requires separate direct evidence.

The 14.10 official release notes report security fixes without component or CVE detail. Sony lists WebKit_1400 as applying to PS5 software 14.00 onward, but the available source listing does not establish that its snapshot maps exactly to build 26.06-14.10.00. Public 14.10 community reports add browser and kernel research claims, but their hardware provenance and CVE/source correspondence are not independently authenticated here. The two 32-byte runs at offsets 0x200 and 0x3E0 are a reproducible observation from one locally hash-verified package; recurrence and field meaning remain unknown. The inner PUP remains inaccessible to this project as a safely supported plaintext format.

## Highest-value open questions

1. Map Sony's official WebKit/JSC source snapshots to the exact 26.06-14.10.00 build. This is the best current PC-only question: direct Sony source listings exist, while source/build identity is the missing evidentiary link.
2. Authenticate the provenance of 14.10 community reports using preserved public records and source lineage, without running probes or contacting hardware.
3. Identify explicit Sony kernel source/build correspondence for upstream FreeBSD advisories before drawing any 14.10 patch conclusion.

Question priority is the weighted mean of five 1–5 scores: firmware relevance (30%), evidence quality (20%), likelihood of an answer (20%), safe PC-only verification (15%), and community contribution (15%). Ties are broken by answerability, then evidence quality, then question ID. Scores are comparative research-planning judgments, not probabilities. Each row retains the component scores, method, rationale, and stop condition.

## Provenance limitations

The historic 13.60 and 14.00 package acquisition attempt found no sufficient official Sony version-to-digest provenance. No historical package was acquired; cross-version recurrence cannot be assessed. The local 14.10 package and all derived binary measurements remain outside Git. Do not infer encryption, signatures, executable content, exploitability or compatibility from entropy, wrapper fields, or version-labelled upstream code alone.
