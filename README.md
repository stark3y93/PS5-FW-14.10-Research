# PS5 update wrapper research toolkit

This repository contains original Python tools for inspecting the **outer SLB2 wrapper** of a local PS5 update package and for collecting bounded normal-webpage capability observations. It contains no Sony firmware, extracted binaries, keys or exploit payloads. Offline tests use synthetic inputs; optional browser collection connects only to your explicitly bound trusted-LAN PC service.

## PS5 browser capability bridge

The user reports that the original passive page now runs on a real PS5 14.10. Raw target JSON and the exact navigation route are still pending. The new authenticated LAN bridge collects results, schedules five fixed bounded diagnostic categories and exports evidence matrices. It does not unlock debug options or system access. See [setup and exact PS5 steps](docs/PS5_RESEARCH_BRIDGE.md) and [implementation/evidence status](reports/PS5_1410_BROWSER_BRIDGE.md).

```powershell
Set-Location E:\PS5-FW-14.10-Research
# After YOU stop the existing diagnostic server on 8765, reuse its working URL:
python -S tools/ps5_bridge.py --bind 192.168.4.29 --port 8765 --secondary-port 8766
```

Open the printed dashboard URL on the PC and enter its separate dashboard key. On the PS5, reload the already working `http://192.168.4.29:8765/`, pair with the printed pairing key, then run **surface** first. The preserved original passive page is available at `/passive/`. No new PS5 capability is confirmed until real results are collected.

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
node tests/browser_diagnostic.test.cjs
node tests/bridge_suite.test.cjs
node tests/bridge_client.test.cjs
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

For the public thread probes 80a–80k, separately clone the external project and run:

```powershell
git clone https://github.com/ZigZagBoi1/PS5-14.10-Research.git E:\PS5-14.10-Research-external
python -S tools/ps5_research.py --probe-audit 'E:\PS5-14.10-Research-external' --format markdown --output reports\external-thread-rop-audit.md
python -S tools/ps5_research.py --probe-audit 'E:\PS5-14.10-Research-external' --format json --output reports\external-thread-rop-audit.json
```

This read-only mode records the repository commit, commit-blob and checkout-byte SHA-256 values, Git blob IDs, cross-references, terminal/readback observations, and contradictions. It compares the probe index's success labels with the saved evidence. It does not run Lua or connect to a console. For the audited snapshot and conclusions, see [EXTERNAL_THREAD_ROP_AUDIT.md](reports/EXTERNAL_THREAD_ROP_AUDIT.md) and [PROBE_80I_80K_VERIFICATION.md](reports/PROBE_80I_80K_VERIFICATION.md).

Compare two local text snapshots, retaining hashes and a unified diff:

```powershell
python -S tools/ps5_research.py --compare .\source-before.cpp .\source-after.cpp --output derived\source-diff.json
```

The arithmetic and bounds helpers are synthetic models; they do not allocate large buffers or execute target code.

## CSSFontFace source comparison

The detector checks two source files against SHA-256 pins and an audited reference catalog, then reports the backing-lifetime pin and client-membership guard separately. Unknown or modified files cannot become verified findings through a keyword match. Every firmware 14.10 verdict remains insufficient: source-file identity does not authenticate a production component build. See the [deep analysis](reports/CSSFONTFACE_DEEP_ANALYSIS.md), [Sony source provenance](reports/PS5_1410_WEBKIT_PROVENANCE.md) and [evidence gaps](reports/WEBKIT_EVIDENCE_GAPS.md).

These commands download only two small public source files for each audited full commit, verify their pinned hashes, and create new snapshot directories. They install nothing:

```powershell
python -S tools/ps5_research.py --fetch-webkit 0e722583a4d695c7b25f384c61fbf5b59b4c3146 --snapshot-dir derived\css-before --format json --output derived\css-before.json
python -S tools/ps5_research.py --fetch-webkit 5aedb82710ba578f61501106e78f6b25b7f7a558 --snapshot-dir derived\css-after --format json --output derived\css-after.json
python -S tools/ps5_research.py --webkit-compare derived\css-before\snapshot.json derived\css-after\snapshot.json --format json --output derived\css-comparison.json
python -S tools/ps5_research.py --webkit-compare derived\css-before\snapshot.json derived\css-after\snapshot.json --output derived\css-comparison.md
```

Use new paths on repeat runs; source and output overwrites are refused. `--webkit-snapshot PATH\snapshot.json` accepts a local source subset. The manifest uses `schema_version: 1`, a `label`, a `provenance` object, and a `files` list containing `path`, lowercase `sha256`, and `origin_url`. Both source paths must be relative to the manifest directory: `Source/WebCore/css/CSSFontFace.cpp` and `Source/WebCore/css/FontFace.cpp`. An [example Sony-source manifest](research/examples/cssfontface/sony-1400-snapshot.json) pins the independently measured archive members; place it with an authorized source subset before using it. The example contains no Sony source or target-build assertion. An [offline ZIP-member extraction example](research/examples/cssfontface/README.md) reproduces the published-source intake from an authorized local archive.

The five source classifications are `PATCHED — VERIFIED`, `VULNERABLE IMPLEMENTATION — VERIFIED`, `MODIFIED / AMBIGUOUS`, `COMPONENT NOT FOUND`, and `INSUFFICIENT EVIDENCE`. “Verified” describes the source pattern and exact audited file pair. A lifetime-only security backport is reported as mixed/ambiguous with its safeguard states; it is not called an unpatched UAF. The limited lexical detector is not a C++ compiler, and the synthetic callback/reference-count tests are not engine-level vulnerability reproductions.

## Passive browser diagnostic and feasibility audit

**Historical browser-access follow-up:** the earlier investigation did not verify a reliable custom-page route on PS5 14.10. The user has since reported successful passive diagnostic execution; the exact route and raw JSON remain pending. The earlier unsuccessful guide/YouTube/message attempts are preserved in [entry evidence](reports/BROWSER_ENTRYPOINT_EVIDENCE.md), [browser-access findings](reports/PS5_1410_BROWSER_ACCESS.md) and [restricted hosting setup](docs/PS5_DIAGNOSTIC_SETUP.md). For passive PC/LAN runs, prefer the two-file restricted host over a general directory server:

```powershell
python -S tools/host_diagnostic.py --bind 127.0.0.1 --port 8766 --check
python -S tools/host_diagnostic.py --bind 127.0.0.1 --port 8766
# Trusted LAN only: replace this example with your chosen PC adapter's IPv4.
python -S tools/host_diagnostic.py --bind 192.168.1.50 --port 8766
```

Run one serving command at a time and stop with Ctrl+C. This helper never supplies a PS5 navigation route, impersonates a captive portal or changes DNS/proxy/certificates. `--check` prints exact asset hashes and closes. Earlier Phase 4 instructions follow for historical context; the new setup guide incorporates the user's observed restrictions.

Phase 4 adds a passive page and offline JSON importer. See [console/PC instructions](reports/PS5_BROWSER_DIAGNOSTIC.md), [target compatibility](reports/WEBKIT_TARGET_COMPATIBILITY.md), [boundary matrix](reports/SECURITY_BOUNDARY_MATRIX.md) and [feasibility report](reports/JAILBREAK_FEASIBILITY_1410.md). No external-navigation route on the 14.10 guide is assumed. The page checks availability without loading fonts, executing a regression or uploading results.

PC preview (stop the server with Ctrl+C):

```powershell
Set-Location E:\PS5-FW-14.10-Research
python -S -m http.server 8765 --bind 127.0.0.1 --directory diagnostics/browser
```

Open `http://127.0.0.1:8765/` on the PC. Select **Run passive checks**. The editable firmware label cannot turn PC results into a PS5 capture. Console instructions are conditional on an existing ordinary navigation route; a GitHub raw page is not a working HTML host.

Exercise the importer immediately using clearly marked synthetic records:

```powershell
python -S tools/ps5_research.py --browser-diagnostic research/examples/browser/synthetic-complete.json research/examples/browser/synthetic-conflict.json --target-firmware 14.10 --format markdown
python -S tools/ps5_research.py --browser-diagnostic research/examples/browser/synthetic-complete.json research/examples/browser/synthetic-conflict.json --format json --output derived\browser-fixture-audit-new.json
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -S -m unittest discover -s tests -q
node tests/browser_diagnostic.test.cjs
```

Python tests require no dependencies. The page fixtures use the already-installed Node runtime's built-in VM only; if Node is absent, do not install it for the console. Those fixtures test page logic, not an actual WebKit engine. Importer evidence uses SHA-256 plus JSON pointers. A `complete` record is self-reported page completion, never proof of firmware identity, native execution or a vulnerability. Source-version comparisons remain available through `--compare` and `--webkit-compare` above.

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
