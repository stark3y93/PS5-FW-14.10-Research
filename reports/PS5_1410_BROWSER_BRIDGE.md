# PS5 14.10 browser bridge: implementation and evidence status

> Later live audit, 20 October 2026: genuine target bridge records are now preserved in the [storage/file audit](PS5_STORAGE_FILE_AUDIT_20261020.md). The implementation-time evidence status below is retained as history. Four new jobs yielded 41 automatic observations, followed by owned-storage cleanup. Picker, file reading and saved-download outcomes remain unverified.

Date: 2026-10-20. This report separates user-reported target observations, PC browser smoke evidence and synthetic regression tests. No exploitation or automated console operation was performed.

## Target evidence received

The user reports successful execution of the existing passive diagnostic on their PS5 14.10 through a PC-hosted LAN URL. JavaScript, Promise, Map, Set, Symbol, BigInt, ArrayBuffer, Uint8Array, TextEncoder, FontFace, TransformStream, fontSet, CSS Grid and CSS font-family checks reportedly worked. WebAssembly and secureContext reportedly returned false. The reported user agent identifies PlayStation 5 / 14.10 and AppleWebKit/605.1.15.

**Evidence source:** the user's message in this research session. **Confidence:** user observation; raw JSON, exact entry sequence and independently recorded target output have not been provided. No artificial target record or capture timestamp was created. This supersedes the earlier lack of a user-reported working page, but does not establish a general browser-entry method for other consoles.

The UA compatibility token does not identify an exact WebKit source revision. API availability does not authenticate firmware, establish memory corruption, demonstrate native execution or verify an exploitable vulnerability. These observations provide no kernel, debug-menu, hypervisor or system-file access.

## Implemented collection

- Standard-library Python bridge with explicit private/loopback IPv4 binding, two fixed local origins and static file allowlists. The original passive HTML/JavaScript files remain unchanged.
- Pairing, memory-only client sessions, separate PC-only dashboard authentication, Host/Origin validation, strict JSON schemas, request/thread/rate/disk limits and fresh evidence directories.
- Fixed allowlisted surface, storage, networking, security and rendering tasks. No arbitrary JavaScript, commands, external addresses or file serving.
- Browser registration, heartbeats, timeouts, partial-job detection, local dashboard, append-only timestamped NDJSON and new JSON/Markdown snapshots with line/hash evidence references.
- Manual controls distinguish a click or Blob creation from an observed save/open. Only user-selected, exact synthetic fixture content is validated; clipboard/personal file/device reads are absent.
- Six evidence gates with expected/observed values, error, scope, confidence and page context. Server-observed origin/transport and asset hashes accompany self-reported firmware/UA labels.

See [setup, bounds and connection steps](../docs/PS5_RESEARCH_BRIDGE.md), [backend](../src/ps5fwlab/bridge.py), [suite](../diagnostics/bridge/suite.js) and [client](../diagnostics/bridge/client.js).

## Local browser observations

A real PC browser on loopback HTTP exercised all five categories, uploads, dashboard login/scheduling, a second-page storage persistence check, Blob creation and owned-storage cleanup. Controlled networking included fetch/XHR GET and POST, allowed/denied CORS responses, one WebSocket echo, one SSE event, a small stream, timeout and deliberate connection failure. Policy checks exercised sandbox opacity and blocked inline script with positive controls. PC raw events are retained locally under ignored `derived/pc-bridge-smoke-*` directories; they are not published as PS5 evidence.

PC loopback reported a secure context despite HTTP. That is expected under the [Secure Contexts specification](https://www.w3.org/TR/secure-contexts/) and illustrates why PC results must not substitute for PS5 LAN HTTP results. No trusted-certificate PS5 HTTPS comparison was performed. WebAssembly absence over one HTTP context does not establish permanent disablement; HTTPS support must also be observed rather than assumed. The suite only validates a minimal module where possible; see the [WebAssembly JavaScript API](https://webassembly.github.io/spec/js-api/).

WebSocket handling follows the bounded single-message subset of [RFC 6455](https://www.rfc-editor.org/rfc/rfc6455). EventSource sends one correctly formatted synthetic event and the client closes it, using the [HTML server-sent events format](https://html.spec.whatwg.org/multipage/server-sent-events.html). These are controlled application checks, not protocol fuzzing.

No actual PC or PS5 file save/open was established by this smoke test. Blob creation remains a user-interaction gate until its outcome is observed. No new PS5 run was performed by the coding agent.

## Regression coverage and review

Python bridge tests cover input/credential validation, host/origin restrictions, protected results, allowlisted tasks, client/job ownership, completion/missing rows, evidence bounds and fixture endpoints. JavaScript fixtures cover restricted getters, HTTP interpretation, owned-storage preservation, allocation bounds, aggregate false positives, failed network controls and manual-file/link handling. The original offline and passive-diagnostic tests remain part of the full run.

An independent code review found that empty manual batches could consume evidence storage, and that object-valued negative probes could be mislabeled available. Regression tests reproduced these failures before fixes. Empty manual batches are now rejected, output is capped at 32 MiB, negative/mixed aggregates have explicit gates, incomplete tasks retain missing-test details, and cleanup preserves ownership collisions. Further regressions ensure failed XHR controls cannot establish controlled-failure causes and mixed language outcomes remain inconclusive.

Final local verification: **136 Python tests run: 135 passed, one Windows symlink-privilege skip; 21 JavaScript tests passed** (eight original passive fixtures, ten capability fixtures, three manual-client fixtures). A missing popup handle remains inconclusive until the actual visible outcome is supplied. No dependencies were installed.

## Next target run

Reuse the user's already working URL after a manual server handoff, pair the PS5, and run surface first. Export raw JSON and Markdown from the PC after the five categories. Then collect reload persistence and each gesture-dependent outcome separately. Preserve all contexts and errors; do not turn a timeout, absent API, missing log or user-agent token into a vulnerability claim. See [exact steps](../docs/PS5_RESEARCH_BRIDGE.md).

**Current conclusion:** the user reports ordinary JavaScript execution; the bridge is ready to collect the missing genuine target capability evidence. Access to every PS5 subsystem is not available from this suite, and no new vulnerability or jailbreak has been verified.
