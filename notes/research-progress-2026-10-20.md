# Research progress — 20 October 2026

## Completed by six agents

1. **Research Intelligence:** verified the seven requested repositories, pinned their default-branch commits, checked licences and contribution files, and built [`research/`](../research/README.md) with a machine-readable evidence ledger and ranked questions. A verifier required correction of compatibility evidence classes before acceptance.
2. **Firmware Analysis:** reviewed the SLB2 parser, entropy sampler and comparator, and fixed a concrete survey-planning validation gap. An impossible earlier sampling design now raises `ValueError`; a synthetic regression covers it. No other code issue was changed without a reproducible case.
3. **Public Vulnerability Research:** documented Sony, FreeBSD and Apple primary disclosures separately from PS5 project claims. The [ledger](public-vulnerabilities-2026-10-20.md) finds no verified 14.10 applicability for the reviewed CVEs or public chains.
4. **Open-Source Engineering:** produced [four pinned upstream proposals](upstream-contribution-proposals-2026-10-20.md). A Relapse README clarification is prepared in a separate local clone at commit `7e07020`; it was not published. Three other proposals need synthetic compiled tests, licence clarification or maintainer preference.
5. **Testing and Verification:** independently checked source claims and all proposed diffs, requested a correction to the knowledge index, and accepted the corrected result. Its [review note](independent-review-2026-10-20.md) records 50 passing synthetic tests and remaining limitations.
6. **Integration and Coordination:** isolated every role in a worktree, preserved the pre-existing integration checkout, cherry-picked accepted commits into this coordination branch, maintained the [task board](multi-agent-plan-2026-10-20.md), and ran the [final local test report](local-test-report-2026-10-20.md).

## Knowledge gained

The older UMTX, SDK and Relapse projects document or gate versions below 14.10. Luac0re's broad wording is an author statement without a pinned 14.10 test. The pup-unpacker requires a previously decrypted input. The two named 14.10 community repositories contain author-reported probes and open questions; neither gives independently authenticated evidence of a complete chain. The exact sources and licence constraints are in the index. A project gate is evidence about its own code, not proof of Sony's patch state.

## Current outcome and next work

The integrated branch adds one defensive code check, one synthetic regression, an indexed source ledger, a public-vulnerability ledger, four upstream proposals, independent review and a reproducible test report. The suite increased from 49 to 50 passing synthetic tests. Only `.gitkeep` placeholders are tracked under `artifacts/` and `derived/`. No real firmware or console was used for this work.

The ranked [research questions](../research/questions.md) focus first on authenticating 14.10 claims, identifying a version-bound component/patch source, and establishing official historical package provenance. No reviewed evidence establishes a 14.10 jailbreak. Future parser proposals need synthetic fixtures and compiled regressions; external submissions require explicit owner approval. Existing PRs and `main` were not changed by this team. GitHub Actions remains unavailable under the previously documented billing restriction.
