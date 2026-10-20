# Independent review — 20 October 2026

Review branch: `review/independent-2026-10-20`, based on integration commit `c2d627a`. Review is source-only and synthetic; no firmware file, console, or third-party payload was used.

| Submitted commit | Decision | Evidence and limit |
| --- | --- | --- |
| Agent 2 `6f857f5` (survey prior-design validation) | Accept | The new `prior_samples <= size - window_size + 1` check matches the existing distinct-start precondition in `sample_entropy`. The regression rejects a one-start interval with two prior samples and a two-start interval with three. It changes only caller-supplied plan validation, not the recorded 14.10 measurements. |
| Agent 3 `9d6a9fa` (public vulnerability ledger) | Accept | Independently opened the pinned PS5 project sources and Sony, FreeBSD, and Apple advisories. The text correctly distinguishes FreeBSD and Apple advisories from PS5 project claims, and says 14.10 applicability remains unknown. Relapse's pinned source list ends at 13.60; that code gate is not proof of a Sony patch. |
| Agent 1 `b037736` plus correction `0de344d` (knowledge index) | Accept after correction | Initial JSON classified several README firmware assertions as direct source observations. The correction marks them `author_claim` and keeps tree/licence observations separate. JSON parses with seven distinct repositories, full pinned commit IDs, and 18 evidence entries whose kinds belong to the schema and URLs contain the matching commit. Directly checked key pinned READMEs and the ZigZagBoi1 contribution guide. The two 14.10 repositories' device results remain author reported; the index makes no complete-chain claim. |
| Agent 4 `345fa86` (upstream proposals) | Accept as proposals | Independently inspected pinned `ps4tools` extraction loop, `ps5-pup-unpacker` reader and field widths, PS5SDK CMake default, and Relapse's allowlist gate. The four issues are specific and source supported. Only the Relapse README draft is locally patched; the other three remain proposals pending synthetic fixtures or maintainer preference. Lack of a root licence for the unpacker is flagged before distributable code work. |

## Reproduction

After cherry-picking Agents 2 and 3 into this isolated review branch, `PYTHONPATH=src python -S -m unittest discover -s tests -v` passed **50/50** synthetic tests. The source index parsed as valid JSON; static assertions found seven unique repositories, seven 40-character commit IDs, and every evidence URL pinned to its row's commit. In the separate Relapse draft clone, a static check found 33 distinct versions, omitted 13.50 and 14.10, confirmed the source gate rejects unlisted versions, and confirmed the README links to that gate. `git diff --check` passed in both review and upstream draft branches. `git ls-files artifacts derived` listed only `.gitkeep` placeholders. This is local correctness evidence for the source changes, not firmware compatibility evidence. No GitHub Actions run was attempted because the existing integration report documents a billing restriction.

## Limits

The PS4 parser and PS5 unpacker proposals are source-level diagnoses. No compiled synthetic regressions were supplied for them. The Relapse draft is documentation only and was not pushed or sent. No current authenticated PR-state or GitHub Actions run was available to this reviewer. The coordinator should inspect the final integrated tree and rerun the synthetic suite after accepting these commits.
