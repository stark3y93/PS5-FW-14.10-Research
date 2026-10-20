# PS5 14.10 jailbreak feasibility

Audit date: 20 October 2026. **No reproducible 14.10 jailbreak is established by this project.** Technical feasibility is unresolved, not disproved. The new work improves target-source evidence and passive evidence collection; it grants no console capabilities.

## What changed in Phase 4

- Fresh Sony records still provide family-level source attribution rather than an exact production executable mapping.
- Additional official ZIP members show that **TransformStream already contains the relevant size/type validation safeguards**, even though its version file follows an old baseline. This is a concrete counterexample to treating an old version string as a global unpatched verdict.
- The published `UnlinkedMetadataTable.cpp` exactly matches the old upstream baseline. The precise upstream overflow-fix commit was located and compared. This upgrades the source evidence for that candidate, without validating the old string-corruption claim or establishing target exploitability.
- A passive browser diagnostic, bounded offline importer, synthetic contradictory examples and JSON/Markdown feasibility output are available. No PS5 diagnostic capture was obtained during this task.

## Evidence-ranked feasibility matrix

Ranks indicate the value of resolving uncertainty, not estimated chances of exploitation.

| Priority | Research question | Evidence now | Confidence / feasibility limit | Next safe action |
|---|---|---|---|---|
| 1 | Does the real guide browser include the old CSSFontFace or metadata code? | Sony's 14.xx bundle contains the old patterns; a different component has selective backports. | Source observations strong; actual 14.10 component correspondence UNKNOWN. | Obtain vendor correspondence or authorized exact-build material; compare each affected function. |
| 2 | Can a controlled ordinary page reach the relevant standard APIs? | Guide access is user-reported; new passive page works on PC. | Console navigation and API availability untested. API presence cannot establish memory corruption. | Follow the conditional diagnostic instructions only if normal external navigation exists. |
| 3 | Does the upstream candidate fault under a controlled engine? | Exact CSS lifetime fix and metadata arithmetic fix exist; arithmetic models run offline. | No vulnerable/fixed WebKit engine pair run here. | Use a prepared PC environment, retain build flags and full failure diagnostics; never transfer the regression to the console. |
| 4 | Are public native results independently authentic? | Audited 80j/80k readbacks support reported user-memory writes. | Self-published Lua/app captures are not an independently reproduced guide-browser primitive. | Obtain original provenance and an independent retained recording; current workflow only reviews evidence. |
| 5 | Is there a reachable 14.10 kernel weakness? | Upstream/older-firmware work establishes classes of bugs. | No matched Sony 14.10 flaw, kernel R/W or kernel execution verified. | Compare exact target functions and security policy from authorized material. No syscall fuzzing. |
| 6 | What protected operations remain after kernel access? | Separate older public HV work exists. | This project has not reached kernel access; HV outcomes are goal-specific and firmware-specific. | Track exact supported versions and prerequisites; do not assume an HV bypass grants initial entry. |

The [boundary matrix](SECURITY_BOUNDARY_MATRIX.md) spells out what would constitute evidence at each stage. Kernel data R/W is distinct from native userland code execution, kernel instruction execution and HV access. There is no evidence that one particular undisclosed route is inevitable, and no basis for attaching Gezine's reported Debug Settings result to our WebKit candidates.

## Public hypervisor work: newer does not mean 14.10

The pinned [Byepervisor Reborn README](https://github.com/PS5Dev/Byepervisor-Reborn/blob/ea04f7132b837087f552c57261cb800481a3a910/README.md) describes a 6.xx–13.60 scope, lists 13.20/13.60 support and marks 13.00 untested. Its 14.00 port suggestion is conditional; it supplies neither a 14.00 port nor a 14.10 result. It requires a prior kernel chain and loader, so it does not fill our missing kernel stage. These are author statements, not hardware reproduction by this audit. The [linked writeup](https://github.com/soniciso1/ps5-hv-writeups/blob/e4d8b98390754d7eba7c4ea307a168a7d2e9962d/s3-resume-startup_mp-ap-launch.md) describes a boundary after kernel compromise and has its own narrower proof/portability statements. Preserve the different evidence scopes instead of merging them into a universal support claim.

## What prevents a usable result today

For this repository: no verified custom-page navigation on the console, no target-matched WebKit vulnerability reproduction, no authenticated guide-browser native primitive, no established privilege transition and no verified 14.10 kernel primitive. A menu demonstration elsewhere cannot supply the missing reproducible chain. Protected kernel/HV operations require their own evidence if those are the desired outcome. None of these gaps is resolved by a feature fingerprint or by changing offsets in an older exploit.

## Reconciliation and reproduction

On inspection, [PR #20](https://github.com/stark3y93/PS5-FW-14.10-Research/pull/20) remained open at `5e7c3b1fe63017a933643609995249937f0453b0`, based on `main` at `b39e5b376c8b8741076813c1e0ff831f7720310c`. [PR #21](https://github.com/stark3y93/PS5-FW-14.10-Research/pull/21) remained open at `f650adecbd4e08a2f00da8615c17d99b5485df6c`, based on #20's branch. Phase 4 starts from #21 and targets that branch while the predecessors are unmerged. No merge/rebase/overwrite was performed. After predecessor merges, retarget in dependency order as appropriate.

Baseline suite: 97 Python tests passed. Phase 4 verification commands and the final count are recorded in [RESEARCH_PROGRESS.md](RESEARCH_PROGRESS.md). New page logic is checked with Node's built-in VM; real WebKit/PS5 behavior is not simulated by those fixtures. No dependencies were installed. Source/log originals and prior measured JSON reports remain untouched. Fresh source provenance is in [PHASE4_SOURCE_EVIDENCE.json](PHASE4_SOURCE_EVIDENCE.json); detailed candidate findings are in [WEBKIT_TARGET_COMPATIBILITY.md](WEBKIT_TARGET_COMPATIBILITY.md).
