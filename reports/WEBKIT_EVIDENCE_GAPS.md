# WebKit evidence gaps and stopping criteria

Audit: 20 October 2026. Firmware 14.10 classification: **UNKNOWN**.

| Question | Available evidence | Missing evidence that would change the conclusion |
|---|---|---|
| Which published Sony source? | Official “14.00 -” link; independently verified `WebKit_1400` font-file hashes and version file. | Exact production component/build correspondence for `26.06-14.10.00`. |
| Does the published source contain the old implementation? | Yes: unprotected backing call and unguarded snapshot iteration; exact file matches to pinned upstream source. | Nothing further is needed to establish those particular source bytes. |
| Is the firmware executable vulnerable or patched? | No target browser executable or authenticated patch inventory was available. | Authorized executable/source build mapping with a reproducible function comparison or documented vendor backport. |
| Does the upstream regression fail on this old tree? | Public regression source and logical models; no engine runner was found on this host. | A controlled build and LayoutTest result for the old and fixed engine, with build configuration and source hashes. |
| Is a crash memory corruption? | No target trace or sanitizer output from this investigation. | Target-matched sanitizer/debugger trace or an independently established fault cause. Missing output alone is insufficient. |
| Is native execution or kernel access established? | PR #20's self-published userland marker results are a separate observation. | Browser entry/primitive and any required privilege transitions must each have their own evidence. |

## Priorities after this audit

The single highest-value next step is an **authorized, exact 14.10 browser component/build mapping**: a vendor correspondence record or lawfully supplied component binary with reliable firmware provenance. This would let the source-level result become a target-specific patch assessment. Do not identify firmware through a filename, mutable user-agent string, feature availability, or a caller-set `target_mapping_verified` flag.

A PC-only engine test pair is the next useful behavior experiment if the required WebKit build environment becomes available. It would test whether the public regression exercises the lifetime problem in the selected source, but would still leave the console mapping unanswered. No dependency installation or new engine build was attempted in this phase; the required synthetic tests run with Python only.

CSSFontFace remains a well-supported browser source lead because Sony's published files can now be compared directly with the documented fixes. Its runtime exploitability and its priority relative to all other candidates are unmeasured. The corrected V480 result still rebuts that specific prior string-corruption claim; it does not rule out every MetadataTable hypothesis. JIT-only candidates have lower relevance to the published PlayStation defaults, but unknown production overrides prevent declaring all such paths impossible. The FreeBSD/kernel candidates remain target-unverified.

Further searches of the same source diffs have diminishing returns: the two safeguard states, stable backport sequence and Sony source-file identities are now established. Repeat that work only if the source archive, fix history or target evidence changes. Preserve negative results: no exact firmware revision, no browser binary, no engine-level crash test, no target memory corruption, and no kernel consequence were demonstrated here.
