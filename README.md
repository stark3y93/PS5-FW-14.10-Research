# PS5 update wrapper research toolkit

This repository contains original, read-only Python tools for inspecting the **outer SLB2 wrapper** of a local PS5 update package. It contains no Sony firmware, extracted binaries, keys, payloads, or console networking code. The tests use only synthetic containers.

The [Gezine review](reports/GEZINE_1410_RESEARCH.md), [vulnerability matrix](reports/VULNERABILITY_MATRIX.md), [false-positive audit](reports/FALSE_POSITIVES.md), [patch comparisons](reports/UPSTREAM_PATCH_COMPARISON.md), [firmware compatibility](reports/FIRMWARE_COMPATIBILITY.md), and [research progress](reports/RESEARCH_PROGRESS.md) distinguish public demonstrations, upstream advisories and evidence on this package. Browser logs can be inspected read-only from a separate checkout.

## What it does

| Command | Output | Input protection |
| --- | --- | --- |
| `inspect` | Validated SLB2 header and entry metadata | Bounds-checked parser |
| `entropy` | Evenly spaced byte-window statistics inside declared entries | Bounded reads; no built-in hash check |
| `survey` | SHA-seeded, disjoint aligned-window statistics | Expected SHA-256 checked before and after sampling |
| `map` | Numerical profiles at wrapper region boundaries | Expected SHA-256 checked before and after mapping |
| `compare` | Relationships among two or more local wrapper maps | Distinct expected hashes and file sizes checked |

The parser reads the first 512 bytes and validates declared file ranges, names and entry overlap. It does not parse or extract the inner PUP. `map` fully measures regions up to 1,024 bytes and reads only their first and last 512 bytes when larger. `survey` limits its aligned sampling frame to one million slots to bound memory use; very small window sizes may be rejected. Commands emit numerical JSON to standard output; keep local reports in ignored `derived/`.

## Test without firmware

Python 3.10 or newer is required. There are no runtime dependencies. From the repository root:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -S -m unittest discover -s tests -v
```

The suite creates temporary synthetic SLB2 files. It requires no Sony package, credentials, network access, or PS5.
The integrated suite includes deterministic parser mutations, survey and comparator regressions, and synthetic evidence-audit cases. The GitHub Actions workflow runs the same firmware-free suite on Ubuntu 24.04 with Python 3.12, pinned trusted actions, `contents: read`, disabled persisted checkout credentials, and a five-minute job timeout. GitHub Actions execution is presently blocked by an account billing restriction; local test output is the available execution evidence.

## Unified offline evidence audit

Run from this checkout in Windows PowerShell with Python 3.12. No installation or console connection is needed:

```powershell
python -S tools/ps5_research.py --firmware D:\PS5UPDATE.PUP --sha256 --evidence-root 'C:\path\to\browser-research-checkout' --output derived\evidence-audit.md
python -S tools/ps5_research.py --firmware D:\PS5UPDATE.PUP --evidence-root 'C:\path\to\browser-research-checkout' --format json --output derived\evidence-audit.json
```

The tool inventories both checkouts, parses saved beacon logs, indexes claims and static code patterns with file and line, flags the V480 contradiction and incomplete test endings, compares caller-supplied source snapshots, models checked integer boundaries, and calls this repository's bounded SLB2 parser for PUP metadata. It never decrypts the inner PUP, executes probes, or labels a pattern match as a vulnerability. `--output` refuses to overwrite an existing result; choose a new path on repeat runs. See the [committed sample report](reports/OFFLINE_ANALYSIS.md).

Compare two local text snapshots, retaining hashes and a unified diff:

```powershell
python -S tools/ps5_research.py --compare .\source-before.cpp .\source-after.cpp --output derived\source-diff.json
```

The arithmetic and bounds helpers are synthetic models; they do not allocate large buffers or execute target code.

## Reproduce the 14.10 observations locally

The official PS5 update file must be obtained separately from [Sony's support page](https://www.playstation.com/en-gb/support/hardware/ps5/system-software/). Keep it in ignored `artifacts/`. [Provenance and package identity](notes/provenance.md) record the 14.10 source, size and digest. The expected SHA-256 is `C17384946DF6E5C85B2D72CBEEE2057B165BF90279D9E2A86D527D0778CDAAF6`.

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
$package = 'artifacts\PS5UPDATE-26.06-14.10.00.PUP'
$expected = 'C17384946DF6E5C85B2D72CBEEE2057B165BF90279D9E2A86D527D0778CDAAF6'
if ((Get-FileHash -LiteralPath $package -Algorithm SHA256).Hash -ne $expected) { throw 'Package SHA-256 mismatch' }
python -S -m ps5fwlab inspect $package > 'derived\slb2-metadata.json'
python -S -m ps5fwlab entropy $package --window 65536 --samples 256 > 'derived\inner-pup-entropy-64k-256.json'
python -S -m ps5fwlab survey $package --sha256 $expected --window 65536 --samples 256 > 'derived\independent-survey-14.10.json'
python -S -m ps5fwlab map $package --sha256 $expected > 'derived\wrapper-neighborhood-14.10.json'
if ((Get-FileHash -LiteralPath $package -Algorithm SHA256).Hash -ne $expected) { throw 'Package changed during analysis' }
```

The `entropy` windows can overlap; they are descriptive measurements, not independent random draws. `survey` uses a deterministic seed derived from the package hash. Its zero-hit binomial number is a **conditional model benchmark**, not a formal confidence guarantee for this fixed selection. High entropy does not distinguish encryption, compression, or other causes. A SHA-256 check before and after analysis detects ordinary file changes, but does not make concurrent modification impossible.

`compare` accepts repeated `--package SAMPLE_ID FILE SHA256 EXPECTED_SIZE` arguments. Sample IDs are labels, **not verified firmware versions**. Cross-version interpretation requires independent Sony-controlled version-to-file evidence. Only 14.10 currently meets this project's provenance gate: [historical 14.00 and 13.60 candidate audit](notes/historical-sony-source-audit-2026-10-20.md). No historical packages were downloaded for this repository.

## Findings and limits

- [14.10 wrapper observations](notes/wrapper-neighborhood-14.10.md) include two 32-byte nonzero runs in a fully measured 512-byte pre-entry block. Their recurrence across versions is unknown.
- [Independent 14.10 byte-window survey](notes/independent-survey-14.10.md) records offsets, results and statistical limits.
- [Cross-version comparison](notes/cross-version-comparison-2026-10-20.md) has synthetic validation but no provenance-verified historical input.
- [Evidence matrix](notes/comparison-matrix.md), [source review](notes/source-review.md) and [experiment ranking](notes/experiments.md) separate observations, third-party claims and hypotheses.
- [Parser validation](notes/analysis-14.10.md) covers strict bounds, malformed synthetic headers and the duplicate-name ambiguity policy.
- [Toolkit review and proposed merge order](notes/toolkit-consolidation-review-2026-10-20.md) describe remaining integration work.
- [Integrated branch manifest and merge proposal](notes/integration-2026-10-20.md) records which PR changes are included and which PRs would become redundant.

No command connects to a console or establishes the meaning of unknown SLB2 fields, inner PUP encryption state, executable content, signature validity, exploitability, or firmware compatibility. Keep Sony packages and generated output in `artifacts/` and `derived/`, respectively; both directories are Git-ignored.
