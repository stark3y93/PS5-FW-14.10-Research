# PS5 research knowledge base

This is a source-linked index of public PS5 research and upstream technical evidence, with the project's existing SLB2 observations kept separate from third-party claims. The reviewable seed is [`catalog.json`](catalog.json). It contains no Sony firmware, extracted data, keys, or binary payloads. Public projects are pinned to inspected Git commit IDs; license status is recorded per repository, and absent licenses are not treated as permission to reuse code. The separately gated manual console observation plan is [`../plans/direct-console-observation-plan.md`](../plans/direct-console-observation-plan.md); it has not been approved or executed.

## Current snapshot

Snapshot date: 2026-10-20. The catalog contains **45 indexed source records** (18 repositories and 27 technical/vendor/support documents), **23 deduplicated findings**, **39 finding-to-evidence links**, **27 question-to-source links**, **12 vulnerability records**, **11 components**, **8 ranked questions**, and **4 unresolved contradictions**. All findings carry explicit firmware relevance, including unknown and author-reported claims.

Thirteen findings are `VERIFIED` only for their bounded statements, and ten are author-reported. This does **not** mean any PS5 vulnerability was independently reproduced: the independent-device verification metric remains **zero**. Review each finding's scope and evidence in [`catalog.json`](catalog.json).

The unified catalog preserves PR #13's pinned source index, the later PR #14 evidence and search improvements, and the additional Sony listing metadata and gated observation plan. Structured records consolidate earlier notes; record counts are not counts of new discoveries.

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

The default outputs are local `ps5-research.sqlite3` and `dashboard.html` files in this directory. They are reproducibly generated from `catalog.json` and ignored by Git so the human-reviewable JSON stays the source of truth. Use `--catalog`, `--database`, and `--output` to select different paths. Search is local FTS5 across findings, questions, repositories, source documents, vulnerability identifiers, and researcher/publisher records; results include source links. Terms are treated as literal quoted tokens, not SQL or FTS query syntax. The static dashboard can be opened in a browser without a server or external JavaScript dependencies.

Run the firmware-free project suite from a clean checkout:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -S -m unittest discover -s tests -v
```

The knowledge-base tests build a temporary database from the JSON seed, check cross-references and evidence URLs, exercise search and render the dashboard. They do not access the 14.10 package, a console, or the network.

## Data model and evidence rules

SQLite normalizes repositories, inspected commits, researchers, source documents, firmware versions, components, vulnerabilities, findings, evidence links, questions and contradictions. Every document has a provenance and version/build-scope field; repository snapshots have exact commit IDs and recorded licenses. FTS5 indexes findings, questions, repositories, source documents, vulnerability identifiers, and researcher/publisher records. The `evidence` and `question_evidence` relations preserve citations and what each citation supports, including multiple citations per deduplicated finding or question.

Use these distinctions when reading results:

- `VERIFIED`: only the bounded statement in the summary is supported by the cited source/reproducible measurement. Read the scope and reproduction fields.
- `AUTHOR-REPORTED`: a pinned author states the finding; this project did not independently reproduce it.
- `unknown` / `unresolved`: no conclusion. Missing support is not evidence of a patch or vulnerability.
- upstream FreeBSD, Apple, WebKitGTK, or WebKit advisories establish facts for those upstream/vendor products only. Sony component/build mapping requires separate direct evidence.

The firmware-version dashboard section is a catalog comparison record only: historical packages have not passed Sony's version/provenance gate, so it does not compare package bytes. Sony's release notes report security fixes without component or CVE detail. Sony lists WebKit_1400 for software 14.00 onward and JSC-800 from 8.00 onward; HEAD metadata and selective range reads were performed, but the ~2.77 GB combined source archives were not downloaded in full, and neither listing maps a source revision to build 26.06-14.10.00. The source review matched four WebCore/JSC files in WebKit_1400 to a pinned upstream commit, inspected a PlayStation-specific JSC build setting, and found that the separate JSC-800 bundle reports an older version; see `research/vulnerability-lab/reports/webkit-1410-source-fingerprint-and-execution-gap.md`. Recent WebKitGTK advisories and FreeBSD jail/kernel advisories establish upstream product facts only. Pinned community reports include browser API/runtime, stream-stage, mitigation, and kernel hypotheses; they remain author-reported, and their own status limits do not demonstrate arbitrary read/write, code execution, sandbox escape, kernel access, or a complete 14.10 chain. The two 32-byte runs at offsets 0x200 and 0x3E0 remain observations from one locally hash-verified package with unknown recurrence and meaning. The inner PUP remains inaccessible as a safely supported plaintext format.

## Highest-value open questions

1. Map Sony's official WebKit/JSC source snapshots to the exact 26.06-14.10.00 build. This is the best current PC-only question: direct Sony source listings exist, while source/build identity is the missing evidentiary link.
2. Reconcile project support tables with explicit source-code version gates to distinguish bug-impact claims, tested ranges, and actual chain support.
3. Authenticate the provenance of 14.10 community reports using preserved public records and source lineage, without running probes or contacting hardware. The next kernel-specific question is whether Sony source/build metadata identifies any FreeBSD-derived revisions.

Question priority is the weighted mean of five 1–5 scores: firmware relevance (30%), evidence quality (20%), likelihood of an answer (20%), safe PC-only verification (15%), and community contribution (15%). Ties are broken by answerability, then evidence quality, then question ID. Scores are comparative research-planning judgments, not probabilities. Each row retains the component scores, method, rationale, and stop condition.

## Provenance limitations

The historic 13.60 and 14.00 package acquisition attempt found no sufficient official Sony version-to-digest provenance. No historical package was acquired; cross-version recurrence cannot be assessed. The local 14.10 package and all derived binary measurements remain outside Git. Do not infer encryption, signatures, executable content, exploitability or compatibility from entropy, wrapper fields, or version-labelled upstream code alone.
