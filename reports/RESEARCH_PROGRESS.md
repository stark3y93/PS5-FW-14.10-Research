# Research progress — 20 October 2026 (Phase 2 update)

## Verified scope

- Imported prior audit commit `c974a4a` onto the existing PR #19 branch, preserving the prior audit history and #19's security guidance.
- The combined evidence tool reads repository files and optional saved logs only. It does not connect to a console, run JavaScript probes, decrypt the firmware, or install packages.
- Offline suite before this phase: **59 tests passed, 0 failed**. Phase 2 verification adds six synthetic regressions; the current full suite passes **65 tests**.
- The supplied 14.10 package can be identified and outer SLB2 metadata checked. The kernel/browser payload was not decrypted or inspected.
- Browser checkout evidence count is 299 parsed events; the offline audit recorded eight incomplete runs and one V480 contradiction. V480 corrected output reports `0-of-14`, rebutting that specific string-corruption signal.
- Public Gezine evidence supports a Debug Settings demonstration and a statement that the 13.xx kernel method was patched in 14.00. The 14.10 method remains undisclosed. The latest inspected external commit (`9c89819cf74002b616108bd674b398ae919b40b6`) includes a newer 80k output than the earlier scan-only capture: its Lua source and 224016 log align on three initialized values and three post-call readbacks. An 80j capture likewise records a before/after marker. These self-published captures support reported userland writes; they do not establish kernel execution or a 14.10 vulnerability.
- External probes 80a–80k were cross-referenced across 11 source files and 28 matching captures. The analyzer reports 80c as contradicted by an unchanged marker, 80i as claimed but not demonstrated (four captures stop at the call), and 80j/80k as supported by operation-result lines (80k lacks its later final banner). One completed 80j run also returns an unchanged marker. Other probes remain partial or incomplete diagnostics. The probe index's `OK` claims exceed saved evidence for 80a–80i. Exact commit/worktree SHA-256 digests, Git blob IDs, commit links and selected evidence lines are in `external-thread-rop-audit.json`.
- The external thread result does not change the local target-compatibility assessment for CSSFontFace or MetadataTable. No Sony PS5 14.10 WebKit/JSC source or authorized browser binary was available for a version match. No firmware-specific vulnerability has been verified.
- The combined offline report reprocessed **299** browser events, found **eight** incomplete runs and one V480 contradiction, and parsed the supplied firmware wrapper metadata without exposing its inner payload.

## Evidence-weighted status

| Gate | Status |
|---|---|
| 14.10 package wrapper provenance | Verified locally by hash and SLB2 parser |
| Upstream CSSFontFace use-after-free | Confirmed upstream; target mapping unknown |
| Metadata size arithmetic | Reproduced synthetically; target allocation/corruption unknown |
| Corrected V480 81,400-length claim | Contradicted by 0-of-14 corrected test |
| Gezine 14.10 debug-menu result | Publicly reported; original media not independently replayed |
| Public 14.10 userland progress | 80j/80k source and self-published raw captures support marker writes; hardware identity/capture authenticity not independently verified |
| 14.10 kernel vulnerability / kernel R/W | Not established in this audit |
| Full jailbreak / hypervisor access | Not established |

The audit is closer to reliable evidence classification and a repeatable offline workflow. It has not moved the target-specific kernel vulnerability or kernel read/write gates. Do not convert this progress into a numerical probability of a jailbreak.
