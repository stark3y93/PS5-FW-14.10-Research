# Research integration candidate — 20 October 2026

## Branch and provenance

`integration/research-toolkit-2026-10-20` was created from the fetched `origin/main` commit `7dd3306`. It fast-forwarded through PRs #7, #8, #9, #10 and #11 in ancestry order. The five PR heads and their original commits remain unchanged. No merge was made into `main`.

PR #4 was reviewed separately. Its workflow changes were incorporated without its older README text, which would have replaced the consolidated setup guide. The workflow now uses pinned `actions/checkout` and `actions/setup-python` commits, `contents: read`, disabled persisted checkout credentials, a five-minute timeout, and firmware-free tests without artifact upload. GitHub Actions execution remains blocked by the account billing lock; this integration does not bypass it.

PR #5 was reviewed separately. Commit `509f97e` was cherry-picked for the duplicate-name ambiguity policy and eight additional synthetic parser tests. Its nonduplicated parser-audit and reproduced-profile notes were incorporated. Its old README sentence was folded into the current README instead of restoring an older copy. The duplicate-name rejection is a conservative parser policy, **not** an assertion that all valid SLB2 variants forbid duplicates.

PR #6 was also checked because it is another open research branch. Its dated compatibility evidence ledger and upstream-head audit were retained. Its older README and experiment ranking were omitted because the survey and wrapper map it recommended have since been performed in PRs #7 and #8; the fixed-seed survey also cannot support a formal binomial confidence claim.

## Validation and limits

- The inherited 41 regression tests from #11 and the eight distinct #5 parser tests pass together: **49/49** with `PYTHONPATH=src python -S -m unittest discover -s tests -v` on this PC.
- The ignored 14.10 source package still matches SHA-256 `C17384946DF6E5C85B2D72CBEEE2057B165BF90279D9E2A86D527D0778CDAAF6`.
- Firmware and generated JSON remain under Git-ignored `artifacts/` and `derived/`. The final tracked-file audit found no Sony binaries, extracted bytes, credentials or generated research outputs. The source and synthetic tests are the publishable material.
- The 14.00 and 13.60 Sony-hosted candidate objects are still excluded. Their version-to-URL and digest claims have only third-party archived XML support; Sony's current pages and live manifest bind only 14.10. No historical package was downloaded or compared. The two 32-byte 14.10 pre-entry runs therefore have no verified cross-version status.
- The SHA-seeded survey's zero-hit statistic is a conditional model benchmark, not a formal 95% confidence guarantee. High entropy does not identify encryption or compression.

## Proposed approval path

1. Review the final integration diff from `main`, especially the #11 regression fixes, #5 parser policy and #4 workflow. Leave every existing PR unmerged while reviewing.
2. If approved, merge the integration branch to `main` once. PRs #7–#11 then become redundant as merge vehicles because their code and documentation are already in the integrated history; #4, #5 and #6 likewise become redundant because their validated, still-current changes are included. Close those PRs with references to the integration merge rather than merging them again. No force-push or retargeting is needed for this approach.
3. After any merge, rerun all firmware-free tests on `main` and verify the final tree against this branch. Do not interpret the billing-blocked Actions state as a test failure.

This branch is a source-only, PC-only toolkit integration candidate. It does not establish a historical firmware version binding, inner PUP format, encryption state, signature validity or jailbreak compatibility.
