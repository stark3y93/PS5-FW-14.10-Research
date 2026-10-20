# Research progress — 20 October 2026 (Phase 2 update)

## Verified scope

- Imported prior audit commit `c974a4a` onto the existing PR #19 branch, preserving the prior audit history and #19's security guidance.
- The combined evidence tool reads repository files and optional saved logs only. It does not connect to a console, run JavaScript probes, decrypt the firmware, or install packages.
- Offline suite before this phase: **59 tests passed, 0 failed**. Phase 2 added six synthetic regressions and ended with **65 tests passed**.
- The supplied 14.10 package can be identified and outer SLB2 metadata checked. The kernel/browser payload was not decrypted or inspected.
- Browser checkout evidence count is 299 parsed events; the offline audit recorded eight incomplete runs and one V480 contradiction. V480 corrected output reports `0-of-14`, rebutting that specific string-corruption signal.
- Public Gezine evidence supports a Debug Settings demonstration and a statement that the 13.xx kernel method was patched in 14.00. The 14.10 method remains undisclosed. The latest inspected external commit (`9c89819cf74002b616108bd674b398ae919b40b6`) includes a newer 80k output than the earlier scan-only capture: its Lua source and 224016 log align on three initialized values and three post-call readbacks. An 80j capture likewise records a before/after marker. These self-published captures support reported userland writes; they do not establish kernel execution or a 14.10 vulnerability.
- External probes 80a–80k were cross-referenced across 11 source files and 28 matching captures. The analyzer reports 80c as contradicted by an unchanged marker, 80i as claimed but not demonstrated (four captures stop at the call), and 80j/80k as supported by operation-result lines (80k lacks its later final banner). One completed 80j run also returns an unchanged marker. Other probes remain partial or incomplete diagnostics. The probe index's `OK` claims exceed saved evidence for 80a–80i. Exact commit/worktree SHA-256 digests, Git blob IDs, commit links and selected evidence lines are in `external-thread-rop-audit.json`.
- The external thread result does not establish CSSFontFace or MetadataTable applicability. The later WebKit phase below adds Sony-published source evidence, while exact 14.10 browser binary correspondence and a firmware-specific vulnerability remain unverified.
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

## Deep WebKit phase

- New branch `research/cssfontface-deep-20261020` starts at PR #20 head `5e7c3b1fe63017a933643609995249937f0453b0`. PR #20 and its research branch remain intact; the new PR is stacked against that branch.
- Independently verified prior Sony source findings from the separate `research/unified-evidence-2026-10-20` branch. Validated HTTP ranges and ZIP CRCs retrieved eight selected members; no full Sony ZIP, firmware component or browser binary was published.
- Sony's official “14.00 -” WebKit_1400 bundle has CSSFontFace.cpp SHA-256 `047110c865310422c0ef77c05268841b1ac982bc22120e8c8e265539c713f3ab` and FontFace.cpp SHA-256 `82b68a296b73840857f0947ae533748d86a8f52248d03cd3f4f06176e56ed50a`. Both match pinned upstream `0e722583a4d695c7b25f384c61fbf5b59b4c3146`; published source version is `616.1.27.211.1`.
- Corrected the patch account: `5aedb827…` adds a membership guard; its parent already has the backing pin. The GLib backport `f3d61dae…` changes the backing call, and `f1fff08…` adds the guard afterward. Missing only the guard does not establish an unpatched UAF.
- Verified twelve upstream raw-source / GitHub API blob matches across six source pairs. Five of eight selected Sony files match the pinned upstream files. Platform options, user-agent code and CSSFontFace.h differ; the header removes `virtual` from the destructor declaration, preventing an assumed whole-tree/ABI match. The user-agent browser tokens are fixed strings, so `605.1.15` / `17.0` cannot date the engine or establish patch state.
- Added a standard-library source detector, bounded pinned downloader, source comparison, JSON/Markdown output and 32 offline regression tests. The complete suite passed **97 tests, 0 failed** using Python 3.12 and the documented `PYTHONPATH=src` command.
- Independent code review identified redirect-following and excessive-JSON-nesting failure paths. Both were fixed and independently rechecked: redirects stop before a second destination request, and excessive nesting returns insufficient evidence.
- Rehashed the local PUP to the recorded SHA-256. Only outer metadata was inspected. No engine test runner or authorized 14.10 browser executable was available, and no engine-level memory fault or console experiment was performed.
- Exact 14.10 WebKit source revision, source-to-executable mapping, CSSFontFace runtime vulnerability, browser primitive, kernel access and hypervisor impact remain **unestablished**. Final target classification: **UNKNOWN**.


## Phase 4: passive diagnostic and boundary assessment — 20 October 2026

- Reconciled open PRs #20 and #21 and verified the existing 97-test baseline. Phase 4 branches from #21; neither prior branch was rewritten or merged.
- Rechecked current Sony source labels, official 14.10 release notes and guide navigation documentation. No exact signed browser/component mapping or ordinary arbitrary-URL guide route was established.
- Retrieved four additional official source ZIP members through validated HTTP ranges and CRC checks (73,421,902 bytes transferred; no full archive hash). TransformStream contains the relevant size/type checks; its changes versus the older baseline are selective safeguards. UnlinkedMetadataTable.cpp matches the old upstream file exactly, and its precise upstream overflow fix was located. See WEBKIT_TARGET_COMPATIBILITY.md and PHASE4_SOURCE_EVIDENCE.json.
- Recorded pinned public UMTX, original Byepervisor, Reborn and linked writeup metadata. Their older ranges and prerequisites do not establish a 14.10 chain. No exploit source was run or payload built.
- Added passive HTML/JavaScript with on-screen summary and selectable JSON, a bounded standard-library importer, SHA-256/JSON-pointer provenance, firmware-label consistency filtering, contradictions, unsupported-claim warnings and conservative JSON/Markdown boundary matrices. Existing source comparison remains available.
- Tested the actual page in the PC's Chromium browser: PASSIVE CHECKS COMPLETE and expected capability summary/JSON were visible. This is explicitly not a PS5 observation. No console operation, DNS change, dependency installation or remote hosting deployment occurred.
- Verification at implementation: **113 Python tests passed, 0 failures; 8 JavaScript fixture tests passed**. Commands: `$env:PYTHONPATH=Join-Path (Get-Location) 'src'; python -S -m unittest discover -s tests -q` and `node tests/browser_diagnostic.test.cjs`. New fixtures were observed failing before their implementation. The JavaScript fixtures run in Node VM, not WebKit; upstream crash/stress regressions were not executed.
- Required reports now cover feasibility, conditional diagnostic instructions, source compatibility, separate boundaries and ranked next research. Original source/log result files and earlier generated evidence JSON were preserved.
- Exact production CSSFontFace/metadata presence, a target memory fault, guide-browser native execution, kernel R/W and hypervisor impact remain **unverified**. Highest-value next task: authorized exact-14.10 component/build correspondence.

- Phase 4 independent code review found Markdown link/image injection through filenames. A new regression failed before the entity-escaping fix; the complete 113-test Python suite and eight JavaScript fixtures passed afterward. Review did not authenticate console behavior or independently audit vendor claims; those remain bounded by the primary-source evidence and explicit UNKNOWN target verdict.


## Browser access investigation - 20 October 2026

- Preserved the user's 14.10 observations: Sony guide only, QR-only YouTube linking, a Google URL removed by Safety, successful PC Edge diagnostic, and no console diagnostic run. No failed approach was retried or evaded.
- Recorded ten public source responses with SHA-256 and date qualifications. Historical PS5 assisted Wi-Fi authentication is documented by a network operator; its phone/laptop flow, unnamed firmware and 2022 document date do not prove console-side browsing on 14.10. PlayStation Portal Wi-Fi support is a different-device result. The older YouTube browser tutorial's original datePublished metadata is 28 Jan 2022, last modified 15 Nov 2024, with no tested firmware stated.
- No reliable arbitrary-webpage route or console-side passive JavaScript result was established on 14.10. Captive-portal support on that exact firmware remains unverified, not declared removed. No deceptive account flow, message evasion, DNS/proxy/certificate modification, portal simulator or exploit was used.
- Added a bounded two-asset HTTP host with explicit RFC1918/loopback binding, Host/route allowlists, GET/HEAD, byte snapshots, hashes and a check-and-close mode. Public/wildcard binds, unrelated paths, listing, uploads and asset symlinks are rejected. No admin command or dependency installation. Existing diagnostic HTML/JS remain unchanged.
- Real loopback tests and CLI checks ran. Port 8765 was already occupied and was left untouched; --check succeeded on 8766. No LAN listener or console route was assumed from this PC-only check.
- Complete suite: 126 Python tests run, **125 passed and 1 skipped** (Windows symlink creation needs unavailable OS privilege); **8 JavaScript tests passed**. The skipped test is retained for environments with symlink support; no elevation was requested.
- Required reports: PS5_1410_BROWSER_ACCESS.md, BROWSER_ENTRYPOINT_EVIDENCE.md and docs/PS5_DIAGNOSTIC_SETUP.md. Source provenance is BROWSER_ACCESS_SOURCE_PROVENANCE.json. Prior PRs #20/#21/#22 remain open; this branch starts from #22 and preserves their history.

- Browser-host independent review found no Critical/Important issue; additional raw request checks confirmed strict routes. The date-description inconsistency was corrected, and all ten source hashes were checked against retained raw responses by the author. Review does not establish console behavior or LAN/firewall reachability.
