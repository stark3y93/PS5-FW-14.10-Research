# False positives and unsupported conclusions

All `analysis/`, `docs/`, `probes/`, and `results/` citations below refer to the separate user-supplied browser research checkout, whose Git remote differs from this repository. Its original logs were read, not copied or altered here.

## Disproven string corruption

`analysis/false-positive-81400.md:8-35` identifies the arithmetic error: an 814-character `'A'` literal was appended 100 times, yielding the expected length 81,400. The older `docs/PROGRESS_AUDIT.md:21` and `docs/PROBE_INDEX.md:20` classified that length as corrupted. The corrected `probes/metadata-overflow/extraction/p480-fixed-literal.js:24-36` builds a measured 1,000-character chunk. The recorded 14.10 run reports `V480-CHUNK-LEN` 1000 (`results/beacon-logs/v480-fixed-literal-results.txt:2`), `V480-post-compile-HITS` 0-of-14 (`:11`), unchanged sampled characters (`:12-14`), and `V480-NO-CORRUPTION` (`:16`). This refutes the **specific string-length signal**; it does not prove every possible overflow path safe.

## Conclusions not supported by committed evidence

- `docs/bugs/metadatatable-overflow.md:3,55-74` calls PS5 heap corruption confirmed and assigns a late crash to an out-of-bounds sweep. The raw record at `results/beacon-logs/session10-beacons.txt:192-193` has `COMPILED-OK` and `CALLING`, then no definitive ending. There is no crash dump, fault address, allocation trace, or test proving causation.
- `docs/bugs/cssfontface-uaf.md:3,72-80` says the upstream fix is absent from the 14.10 build. This checkout has no Sony WebKit binary/source comparison and no recorded V445/p170 crash. Upstream vulnerability is real; PS5 applicability remains unknown.
- `docs/bugs/transformstream-disconnect.md:3,30-53` assigns the local substitution to CVE-2026-43705 and reports V429/V431 device observations, but the original logs are absent. The cited CVE is real upstream; exact Sony behavior and impact are unconfirmed here.
- `docs/bugs/tee-type-confusion.md:28-44` describes a one-element iterator crash and attributes it to a bounds trap. No fault log establishes that cause; a process exit or missing beacon alone would not.
- `docs/KERNEL_AUDIT.md:7-29` ranks public FreeBSD CVEs as if their code were present in Sony's fork. Upstream advisories do not establish PS5 14.10 reachability, patch state, or exploitability.
- `docs/FINDINGS.md:31-39` calls the font `loca` test a confirmed out-of-bounds read. The cited malformed-font acceptance and canvas rendering do not distinguish a protected fallback glyph from an out-of-bounds memory disclosure, and the underlying V180A capture is absent.
- `docs/FINDINGS.md:27-31` describes a `CSSFontFaceSet::matchingFacesExcludingPreinstalledFonts` lifetime hypothesis, whereas `docs/bugs/cssfontface-uaf.md:11-47` describes the upstream `CSSFontFace::iterateClients` UAF. They are different mechanisms and must not be treated as one confirmed PS5 bug.
- `docs/PROGRESS_AUDIT.md:31-40` infers precise WebKit source generation and allocator properties from a reported user agent and reference source. The local PUP cannot validate these code-level assertions.

**CVE hygiene:** CVE-2026-43715, CVE-2026-43705, CVE-2026-64784, CVE-2026-7270, and CVE-2026-45251 are real public identifiers, linked in the matrix. The disputed part is their mapping and applicability to this PS5 firmware. Other identifiers in the repository require individual advisory-to-code validation before prioritization.
