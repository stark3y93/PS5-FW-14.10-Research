# Unified evidence integration log — 2026-10-20

## Integrated history

The isolated branch `research/unified-evidence-2026-10-20` is based on `origin/main` commit `46ebfc78eec7d863af1d73003681b1dc0fc44944`. It preserves and merges:

- PR #13 head `da5114413e3cadcc34dcebcc4c1b8c9ea93073c2` — merge commit `5608dcd`.
- `research/vulnerability-lab` head `b4f7b456789c712fde8aa345879d7139981fb8c8` — merge commit `240ac96`.
- `research/max-intelligence-2026-10-20` head `c25f02c3ad9147400dd23184c830d1b70d14335e` — merge commit `a7051bd`.

The merge commits preserve source branch ancestry. The publication audit remains separate. Other active research worktrees were not edited, checked out, rebased, or reset.

## Evidence model and current corpus

The checked-in JSON catalog is the durable source of truth. It currently indexes 18 pinned public Git repositories, 23 technical/vendor/support documents, 20 deduplicated findings, 32 finding-to-source relations, 10 firmware-version records, 9 CVE records, 11 components, 8 ranked questions, and 3 unresolved contradictions. Repository references preserve the inspected commit, observed head when available, license status, coverage level, and links with assertion scope. See `source-coverage.md` and `catalog.json`.

Thirteen `VERIFIED` labels mean that the narrow statement is supported by its cited source or a reproducible local synthetic/metadata observation. Seven findings are `AUTHOR-REPORTED`. The catalog has **zero independently reproduced PS5 vulnerability findings** and no device tests. These classifications apply only to each finding's stated scope.

## New primary-source checks

### Sony WebKit and JavaScriptCore listings

- Sony WebKit OSS page: <https://www.playstation.com/en-us/oss/ps5/webkit/>. It labels `WebKit_1400` for PS5 software 14.00 onward and links `WebKit_1400.zip`.
- Sony JavaScriptCore OSS page: <https://www.playstation.com/en-us/oss/ps5/webkit-javascriptcore/>. It labels `JSC-800` for PS5 software 8.00 onward and links `JSC-800.zip`.
- HEAD metadata was read without downloading the archives. `WebKit_1400.zip`: 1,637,794,253 bytes, Last-Modified 2026-10-15, ETag `0x8DF2A837F34C6C7`. `JSC-800.zip`: 1,369,859,528 bytes, Last-Modified 2026-08-07, ETag `bf49658547d459e0405ba5cba59cb1d6:1786126791.99314`. These ETags are HTTP validators, **not** cryptographic content hashes.
- The two archives total about 2.77 GB and expose no exact source commit/build mapping on the listing. They were not downloaded. Thus no source-level patch comparison against the Sony archives was possible in this pass. `WebKit_1400`/`JSC-800` labels do not prove exact correspondence to build 26.06-14.10.00.

### WebKit advisories and CVE lineage

- WebKitGTK/WPE [WSA-2026-0004](https://webkitgtk.org/security/WSA-2026-0004.html) lists CVE-2026-43715 as an upstream memory-safety issue, with WebKitGTK/WPE affected versions before 2.52.5. Red Hat's [CVE-2026-43715 record](https://access.redhat.com/security/cve/cve-2026-43715) describes a use-after-free and links Bugzilla 313577. Bugzilla denied access during this audit, so the exact WebKit fix commit was not independently retrieved.
- The more recent [WSA-2026-0005](https://webkitgtk.org/security/WSA-2026-0005.html) (2026-08-20) and [WSA-2026-0006](https://webkitgtk.org/security/WSA-2026-0006.html) (2026-09-29) were added as dated source records. WSA-0006 includes many CVE entries, some concerning bundled third-party components; scope is per individual entry and product. These are WebKitGTK/WPE statements and do not transfer to Sony's product.
- The 14.10 community report's CSSFontFace claim and the upstream CVE-2026-43715 use-after-free are **not shown to be the same flaw**. The possible association remains author-reported/hypothesis only. No PS5 vulnerability or patch state is established.

### Kernel evidence

- FreeBSD [SA-24:14.umtx](https://www.freebsd.org/security/advisories/FreeBSD-SA-24:14.umtx.asc) verifies CVE-2024-43102 within the upstream FreeBSD branch scope. That scope is not Sony source mapping.
- The catalog also indexes official FreeBSD [SA-26:13.exec](https://lists.freebsd.org/archives/freebsd-security/2026-April/000448.html), [SA-26:19.file](https://security.freebsd.org/advisories/FreeBSD-SA-26:19.file.asc), and other source-advisory records. The upstream issue and correction are evidence only for their named FreeBSD releases/commits. Community attribution of a related bug to PS5 does not demonstrate shared source revision, exploit reachability, or 14.10 affected/fixed status.
- No exploit, proof-of-concept, or trigger was executed. No kernel source from a PS5 package was extracted.

### Historical package provenance leads

The MewX firmware index was added at pinned commit `83b0b510580bdbf3a2b77c05ccc7566e887be60d`, with a second 13.60 XML reference pinned at `7f4ed6a8d7395d22e260563a189756ec6308ca46`. Those archived files contain 14.00- and 13.60-labelled update-list records with Sony CDN metadata. As recorded in `notes/historical-sony-source-audit-2026-10-20.md`, a Sony-hosted object/metadata check did not provide sufficient official version-to-full-file digest provenance for cross-version analysis. No firmware object was downloaded. This source is a provenance lead, not a verified comparison sample, and its licence remains unverified.

## Contradictions and negative results

- Sony release notes say unspecified security fixes; they do not name CVEs or components.
- Sony's current source labels establish version ranges but not an exact source revision for 14.10. No source/build mapping was found in the public listing or HEAD metadata.
- The upstream WebKitGTK CVE identity is verified within WebKitGTK scope; equivalence to the community CSSFontFace claim is unverified.
- FreeBSD upstream UMTX and other CVE fixes are documented, but Sony's matching code, patch status, and 14.10 applicability remain unknown.
- Existing exploit repositories have older version gates/ranges. Their listed range ceilings do not prove that a bug is patched after the ceiling, and no complete 14.10 chain is verified.
- Cross-version SLB2 recurrence remains untested because historical package identity/provenance is insufficient. The existing single-package 14.10 byte runs remain observations with unknown meaning.

## Reproduction and verification

From a clean checkout, generate the database and dashboard locally (generated files are ignored and reproducible from `catalog.json`):

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -S -m ps5knowledge build-db
python -S -m ps5knowledge stats
python -S -m ps5knowledge search 'WebKit Sony'
python -S -m ps5knowledge dashboard
python -S -m unittest discover -s tests -v
```

The integrated synthetic suite passed **57/57** after the three branch merges. The knowledge-base tests build a disposable SQLite database, validate references and source URLs, verify FTS search and render the dashboard. These tests make no network or console calls and do not read firmware. Hosted Actions remains unverified because the observed GitHub runs started no jobs.

## Direct-console gate

No console observation is authorized by this log. Sony's [support instructions](https://www.playstation.com/en-us/support/hardware/playstation-system-software-application-version/) document Settings → System → System Software → Console Information for the displayed version, and note that the screen also shows network identifiers. The separate plan at [`../plans/direct-console-observation-plan.md`](../plans/direct-console-observation-plan.md) therefore limits capture to a manual version transcription and excludes screenshots and network identifiers. Execution requires the owner's explicit approval of that plan. No payload, protection bypass, firmware update, or console connection is included in this integration.
