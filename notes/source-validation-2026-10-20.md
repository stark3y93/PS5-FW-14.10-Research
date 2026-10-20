# Sony source validation, 2026-10-20

## Scope and provenance

This phase uses only Sony's public [WebKit](https://www.playstation.com/en-us/oss/ps5/webkit/) and [JavaScriptCore](https://www.playstation.com/en-us/oss/ps5/webkit-javascriptcore/) archives and the [upstream WebKit commit b21a503](https://github.com/WebKit/WebKit/commit/b21a503b579a8ab14c839f82cc77176e507352e5). Apple identifies the same WebKit Bugzilla item, 302502, in its [CVE-2025-43529 advisory](https://support.apple.com/en-us/125884). Apple's affected-product statement does not transfer to PS5.

The two complete ZIPs are retained locally under ignored `artifacts/sony-oss/`; their URLs, sizes, SHA-256 digests, entry counts and source markers are in [source-archive-analysis-2026-10-20.json](source-archive-analysis-2026-10-20.json). Reproduce that report with `python -S research/source-validation/analyze_archives.py`. No source archive or Sony code is committed.

Sony labels WebKit `14.00 -` and JavaScriptCore `8.00 -`. The WebKit archive declares `616.1.27.211.1` in `Configurations/Version.xcconfig`; the JSC archive's `Source/JavaScriptCore/ChangeLog` starts 2022-03-25. Neither marker independently identifies build `26.06-14.10.00`, a Git commit, the exact compiled binary, or enabled DFG settings. The ZIP HTTP modification dates are publication metadata, not source revision dates.

## Patch comparison and limits

Upstream b21a503 adds traversal of transitively incoming Phi values when the DFG store barrier phase marks an escape. `WebKit_1400.zip` contains `Source/JavaScriptCore/dfg/DFGStoreBarrierInsertionPhase.cpp` with direct epoch marking in the compared sites, and lacks `forAllTransitiveIncomingValues`. The older `JSC-800.zip` also lacks that call, but its function structure differs, so it is not an exact pre-patch match. This supports a bounded **published-source delta**, with high confidence in the file text. It does not establish a PS5 14.10 vulnerability or an exploitability claim. An equivalent backport elsewhere, a different compiled source, or inactive optimization could change runtime relevance.

The existing [WebKitGTK advisory](https://webkitgtk.org/security/WSA-2026-0004.html) and 14.10 community reports remain upstream or author claims in the knowledge base. This phase did not find a commit-to-Sony-source match for their named CVEs, so no product finding was promoted from those records.

## PC-only tests and failed experiment

| ID | Method | Observed result | Limit |
|---|---|---|---|
| `e-model-first-build` | VS clang-cl default target with x64 libraries | Failed link with machine-type mismatch and unresolved CRT symbols. | No behavioral result. |
| `e-model-asan` | `research/source-validation/run_phi_model.bat` with x64 clang-cl `/fsanitize=address` | Exit 0; original model assertions distinguish direct Phi marking from transitive incoming marking. ASan printed `interception_win: unhandled instruction` on this host. | Model is original code, not WebKit or Sony runtime. |
| `e-asan-positive-control` | `research/source-validation/run_phi_model.bat probe` | Exit 1 as expected; ASan reported heap-buffer-overflow at `asan_probe.cpp:5`. The same interception warning appeared. | Confirms local ASan detects this simple violation only. |

The model and probe run on this Windows PC. They do not access a PS5, a firmware package, a browser, or a remote endpoint. All outcomes, including the failed compiler attempt, are stored in the `experiment` table of the generated SQLite database and shown in the dashboard.

## Strongest next PC-only experiment

Pin the Sony WebKit archive to an upstream source revision using multiple exact file hashes against upstream Git history, then compare the full b21a503 context and any Sony-specific changes. If revision mapping remains ambiguous, stop at the source-delta result. A full JSC engine build with upstream's regression test would be a separate, larger PC-only step after the revision is pinned.
