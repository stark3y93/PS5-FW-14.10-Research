# Offline PS5 research evidence report

Root: `<repository root>`

Inventoried 48 files; parsed 0 log events; indexed 81 claim lines.

## Inventory

(none): 5, .json: 1, .md: 25, .py: 15, .toml: 1, .yml: 1

## Ranked evidence

1. **V480:** no browser beacon log is present in this root.
2. **CSSFontFace:** no local claim or source in this root.
3. **MetadataTable:** synthetic 32-bit wrap is reproducible; no target source in this root.
4. **Kernel CVEs:** no 14.10 kernel source or result in this root.

## Contradictions

- 81400 string length described as corruption despite corrected V480 result: `derived/combined-audit-20261020.md:102` - 81400 string length described as corruption despite corrected V480 result: `analysis/struct-layouts.md:16` JSString.length() reads from the StringImpl pointed to by m_fiber, not from a field in JSString itself. The `.length = 81400` resul; `notes/1410-vulnerability-evidence-priorities-2026-10-20.md:18` | V480 JavaScript string corruption | Corrected browser beacons: `0-of-14` hits; expected character checks | **Disproven for the corrected test**, not a usable primitive | None for the original claim; archive correction and avoid reassertio

## Nondefinitive log endings


## Static code patterns

- iterator override: 0 hits
- large allocation: 0 hits
- network operation: 0 hits
- native interface reference: 0 hits
These are source-text matches, not identified vulnerabilities.

## Firmware

{
  "present": true,
  "file": "PS5UPDATE.PUP",
  "bytes": 1261408256,
  "container_magic": "SLB2",
  "header_hex": "534c4232030000000000010001000000c8972500000000000000000000000000",
  "visible_marker": "PS5UPDATE1.PUP",
  "sha256": "c17384946df6e5c85b2d72cbeee2057b165bf90279d9e2a86d527d0778cdaaf6",
  "kernel_readable": false,
  "limitation": "Container header only; no decryption or embedded kernel/source verification.",
  "validated_slb2": {
    "file_size": 1261408256,
    "version": 3,
    "block_count": 2463688,
    "unknown_1": 65536,
    "unknown_2": 0,
    "unknown_3": 0,
    "unknown_4": 0,
    "entries": [
      {
        "name": "PS5UPDATE1.PUP",
        "block_offset": 2,
        "offset": 1024,
        "size": 1261406781,
        "unknown_1": 0,
        "unknown_2": 0
      }
    ]
  }
}

## Synthetic arithmetic

{
  "count": 38348816,
  "stride": 112,
  "mathematical_bytes": 4295067392,
  "uint32_bytes": 100096,
  "wrapped": true
}

## Method limits

- Documentation is an assertion, not a firmware source dump.
- A missing end beacon does not identify a crash cause.
- Static pattern matches do not prove memory corruption or reachability.

## Separate browser evidence checkout

# Offline PS5 research evidence report

Root: `<evidence checkout>`

Inventoried 81 files; parsed 299 log events; indexed 155 claim lines.

## Inventory

(none): 12, .c: 1, .html: 1, .js: 33, .json: 1, .md: 24, .py: 1, .s: 2, .sh: 4, .txt: 2

## Ranked evidence

1. **Observed negative control — V480:** `results/beacon-logs/v480-fixed-literal-results.txt:11` reports zero hits in the corrected run. This rebuts the 81,400-length corruption interpretation.
2. **Upstream candidate — CSSFontFace:** local claim `docs/bugs/cssfontface-uaf.md:1`; no confirming crash log or PS5 WebKit source in this checkout.
3. **Unresolved — MetadataTable:** local claim `docs/bugs/metadatatable-overflow.md:1`; synthetic 32-bit wrap is reproducible, while PS5 heap corruption is unestablished.
4. **Unresolved — kernel CVEs:** local claim `docs/KERNEL_AUDIT.md:7`; applicability to PS5 14.10 and sandbox reachability are unestablished.

## Contradictions

- 81400 string length described as corruption despite corrected V480 result: `analysis/struct-layouts.md:16` JSString.length() reads from the StringImpl pointed to by m_fiber, not from a field in JSString itself. The `.length = 81400` result from sweep corruption means m_fiber was overwritten to point somewhere that has 81400 at the m_length offse; `results/beacon-logs/v480-fixed-literal-results.txt:11` {"t": "18:13:04", "path": "/beacon/V480-post-compile-HITS", "ua": "Mozilla/5.0 (PlayStation; PlayStation 5/14.10) AppleWebKit/605.1.15 (K", "body": "[8496ms] 0-of-14", "origin": "<REDACTED>"}

## Nondefinitive log endings

- V150G: `results/beacon-logs/session10-beacons.txt:185`, `results/beacon-logs/session10-beacons.txt:193`
- V150H: `results/beacon-logs/session10-beacons.txt:194`, `results/beacon-logs/session10-beacons.txt:195`, `results/beacon-logs/session10-beacons.txt:196`
- V150I: `results/beacon-logs/session10-beacons.txt:197`, `results/beacon-logs/session10-beacons.txt:199`, `results/beacon-logs/session10-beacons.txt:212`, `results/beacon-logs/session10-beacons.txt:213`
- V150J: `results/beacon-logs/session10-beacons.txt:73`, `results/beacon-logs/session10-beacons.txt:77`, `results/beacon-logs/session10-beacons.txt:226`, `results/beacon-logs/session10-beacons.txt:227`
- V150K: `results/beacon-logs/session10-beacons.txt:81`, `results/beacon-logs/session10-beacons.txt:234`, `results/beacon-logs/session10-beacons.txt:239`, `results/beacon-logs/session10-beacons.txt:240`
- V150L: `results/beacon-logs/session10-beacons.txt:96`
- V161A: `results/beacon-logs/session10-beacons.txt:245`, `results/beacon-logs/session10-beacons.txt:246`
- V161B: `results/beacon-logs/session10-beacons.txt:247`

## Static code patterns

- iterator override: 0 hits
- large allocation: 101 hits; examples `probes/metadata-overflow/early/p141-overflow.js:20`; `probes/metadata-overflow/early/p141-overflow.js:45`; `probes/metadata-overflow/early/p141-overflow.js:61`
- network operation: 47 hits; examples `probes/metadata-overflow/early/p142-heap-survive.js:9`; `probes/metadata-overflow/early/p142-heap-survive.js:16`; `probes/metadata-overflow/early/p143-worker-witness.js:11`
- native interface reference: 1 hits; examples `tools/remote-loader/runtime-derive/derive-runtime.js:462`
These are source-text matches, not identified vulnerabilities.

## Firmware

{
  "present": false,
  "kernel_readable": false
}

## Synthetic arithmetic

{
  "count": 38348816,
  "stride": 112,
  "mathematical_bytes": 4295067392,
  "uint32_bytes": 100096,
  "wrapped": true
}

## Method limits

- Documentation is an assertion, not a firmware source dump.
- A missing end beacon does not identify a crash cause.
- Static pattern matches do not prove memory corruption or reachability.
