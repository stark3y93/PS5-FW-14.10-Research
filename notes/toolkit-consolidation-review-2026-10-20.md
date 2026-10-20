# Toolkit code review and integration plan — 20 October 2026

## Review scope and evidence

The local stack is `main` (`7dd3306`) → PR #7 (`9def3fa`) → PR #8 (`267aa8c`) → PR #9 (`e6ccd22`) → PR #10 (`b284996`). Each PR is open and targets its predecessor, except #7, which targets `main`. Diffs were reviewed in that order; no PR was merged or retargeted. The baseline at #10 passed 36 synthetic tests. This consolidation branch starts at #10 and adds focused fixes and tests.

| PR | Review result before consolidation | Required action |
| --- | --- | --- |
| [#7](https://github.com/stark3y93/PS5-FW-14.10-Research/pull/7) survey | Deterministic selection and source caveat are useful. Candidate-slot materialization could exhaust memory for a small window; even entropy samples could silently collapse. The survey also lacked a final hash check. | Carry this branch's slot cap, distinct-start validation and post-survey hash check into the integrated code. |
| [#8](https://github.com/stark3y93/PS5-FW-14.10-Research/pull/8) neighborhood map | Bounded edge sampling and the observed 14.10 pre-entry counts are sound. Two adjacent samples cover 513–1,024-byte regions completely; the method description did not make that clear. | Keep measurements, clarify complete-coverage behavior. |
| [#9](https://github.com/stark3y93/PS5-FW-14.10-Research/pull/9) comparator | Hash and size checks, sample-label caveat and synthetic malformed-container cases are sound. It incorrectly called fully covered two-sample gaps inconclusive and omitted final padding counts. | Carry this branch's profile aggregation and boundary tests into the integrated code. |
| [#10](https://github.com/stark3y93/PS5-FW-14.10-Research/pull/10) provenance | The source distinction is appropriate. Live Sony HEAD responses establish object presence and reported length, while version mapping and digest appear only in third-party archived XML. | Preserve the exclusion decision; do not represent either candidate as a verified historical package. |

The parser's 512-byte header read, block-count equality, bounded entry ranges, ASCII name validation and overlap rejection were independently inspected. Its field labels `unknown_*` appropriately avoid speculative meanings. Its strict name alphabet and 512-byte declared-size equality describe the **accepted subset** of SLB2; they are not proof that every valid Sony variant uses those constraints. The CLI's `inspect` and `entropy` commands do not hash-bind input themselves; the README provides a before/after digest guard for reproduction. `compare` accepts user-supplied sample labels, not authenticated version metadata.

The 14.10 entropy and wrapper measurements are descriptive. Byte entropy cannot distinguish encryption from compression. The fixed SHA-derived survey selection does not justify a formal 95% coverage or confidence statement; its zero-hit figure is a conditional uniform-slot model benchmark. The two 32-byte runs are confirmed in this one local 14.10 wrapper and cannot yet be called version-stable or undocumented: no independently version-bound historical package passed the official-source gate.

Final local verification on this branch: `PYTHONPATH=src python -S -m unittest discover -s tests -v` passed **41/41** synthetic tests, `git diff --check` was clean, and the original ignored 14.10 file still hashed to `C17384946DF6E5C85B2D72CBEEE2057B165BF90279D9E2A86D527D0778CDAAF6`. No real PS5 was contacted.

## Synthetic correction evidence

- An interval with more than one million aligned slots now fails before the survey allocates a list; ordinary 14.10-sized 64 KiB frames remain valid.
- Requests for more evenly spaced window starts than integer positions now fail instead of returning fewer samples than requested.
- A 1,024-byte pre-entry gap whose nonzero run crosses the 512-byte sample boundary is recognized as fully measured and the run is joined. A 513-byte final padding interval now reports all 513 zero bytes.
- A file mutation injected after survey sampling is caught by the final full-file hash check. This check is not a substitute for exclusive access against a malicious concurrent writer.

## Repository and history audit

At this branch point, `git ls-files` shows only source, Markdown, tests, workflow and `.gitkeep` placeholders in `artifacts/` and `derived/`. The `.gitignore` excludes every other path below those directories, plus Python caches and build outputs. Across all locally available refs, `git rev-list --objects --all` found 104 objects; the largest blob was 7,356 bytes, a Markdown note. A scan of historical blob contents for common GitHub/OpenAI/AWS token forms, private-key delimiters and executable/SLB2 file magic at blob start found no matches. This is a targeted audit, not a proof that arbitrary secrets cannot exist. No Sony firmware, extracted binary or generated numerical JSON appears in tracked history.

The committed `main` workflow uses floating action tags and lacks explicit least-privilege permissions. [PR #4](https://github.com/stark3y93/PS5-FW-14.10-Research/pull/4) contains the pinned read-only CI correction and should be integrated before a public release. GitHub Actions remains blocked by the account billing lock; local tests provide the verification evidence here.

## Proposed merge plan; approval required

1. Review this consolidation branch against #10 and retain all corrective commits. It is intentionally stacked so original PR heads and history remain unchanged. A new PR can target `research/historical-sony-source-audit`.
2. After approval, merge or rebase #7 onto `main`, then retarget #8 to `main` and integrate it, followed by #9, #10, and finally the consolidation PR. If using squash merges, retarget each next PR after its predecessor lands and inspect the resulting diff before merging. If using merge commits, the existing ancestry permits the same order without rebasing every head.
3. Resolve the separate [#4](https://github.com/stark3y93/PS5-FW-14.10-Research/pull/4) CI and [#5](https://github.com/stark3y93/PS5-FW-14.10-Research/pull/5) parser-validation branches against the resulting `main`; review overlap rather than blindly applying both. Re-run firmware-free tests after each integration step. Do not interpret a billing-blocked Actions run as a code failure or bypass the restriction.

No existing PR is approved for an as-is merge: #7 and #9 need the corrections above; #8 and #10 are methodologically ready in their respective order once the stack is integrated. The toolkit is appropriate as a source-only research release after corrective integration, the CI security update and a fresh local verification. It is not a validated cross-version firmware analyzer.
