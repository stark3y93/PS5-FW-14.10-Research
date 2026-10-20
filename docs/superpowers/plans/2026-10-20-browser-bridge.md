# Browser research bridge plan and safety contract

Goal: collect genuine, bounded normal-webpage observations on the user's PS5, preserving the working diagnostic unchanged. User-reported first capture: 14.10, JS and listed APIs available, WebAssembly false, insecure HTTP context. Raw JSON and navigation sequence are not yet supplied; do not manufacture an authenticated capture.

Architecture: separate standard-library LAN bridge and second controlled origin, static client/dashboard, exact task catalog, pairing/session tokens and separate PC dashboard credential. Strict Host/Origin/body/schema checks, no arbitrary commands/URLs or file serving. Timestamped append-only evidence and JSON/Markdown snapshots stay in ignored derived/. Optional TLS accepts user-supplied certificate/key only; no certificate installation, DNS changes, console operations or router/firewall changes.

Limits: one task at a time, <=256 KiB allocated buffer, <=4 KiB synthetic storage per store, 16x16 rendering surface, short network deadlines, no filesystem enumeration or personal file/clipboard reads. Downloads/popups/upload selection require explicit local gestures and observer confirmation; a server file request never proves a saved/opened download. Only exact suite-generated text may be uploaded. Device APIs are presence checks, never permission prompts. Storage reads touch suite-owned keys/database only.

Tasks:
- [x] Backend model + auth/validation/allowlisted scheduling, stale/timeout states, bounded WebSocket/SSE and controlled CORS endpoints. Write failing tests first.
- [x] Separate client tasks, manual controls, dashboard and exports. Isolated JavaScript fixtures and real PC browser smoke; do not operate the PS5.
- [x] Documentation, six-gate classification and evidence intake. Explicit HTTP/HTTPS context; absent WASM is not a permanent disablement verdict.
- [x] Run full existing/new suites, independent review, preserve prior results/assets, commit locally. User asked implementation and connection steps; no new push/PR request in this turn.

Review focus: token leakage or result disclosure; forged/malformed uploads; timeout confused with blocked capability; file request confused with download success; unrelated storage/files touched; CORS control failures confused with CORS enforcement; unsafe/unbounded sockets/tasks; false inference of privilege or firmware authenticity.
