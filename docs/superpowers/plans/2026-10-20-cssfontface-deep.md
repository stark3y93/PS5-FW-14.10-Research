# CSSFontFace evidence implementation plan

**Goal:** Compare authorized source snapshots without transferring a source verdict to firmware 14.10.

**Baseline:** PR #20 head `5e7c3b1fe63017a933643609995249937f0453b0`; preserve that branch and stack a new PR against it.

**Design:** A focused standard-library module owns manifest verification, audited full-file SHA-256 references, conservative function recognition, source comparison, Markdown rendering, and logical reentrancy models. The existing research CLI exposes those operations. Unknown source pairs remain ambiguous even when familiar snippets occur. No caller-supplied firmware label authenticates a target.

- [x] Reconcile branches and prior source research; verify the published Sony font-file fingerprints independently.
- [x] Write failing offline synthetic tests for source classification, integrity failures, target attribution, and callback/lifetime models.
- [x] Implement source detector and audited upstream catalog.
- [x] Integrate CLI, test bounded downloads and invalid inputs, and compare real pinned snapshots.
- [x] Correct upstream patch history, document Sony source/build evidence and remaining gaps, and update priorities.
- [x] Run the complete offline suite and resolve independent review findings.

**Publication procedure:** scan staged files, commit, push this new branch, open a PR against the preserved PR #20 branch, and attach it. The user explicitly selected this publication path; no merge or force-push is authorized.

**Review focus:** Comments/strings cannot supply signatures; hash mismatch cannot be ignored; a lifetime-only security backport must not be called unpatched UAF; filename/user-agent/version labels cannot prove a 14.10 source mapping; Sony range reads do not supply a whole-archive hash.
