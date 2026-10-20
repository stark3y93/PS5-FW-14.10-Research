# Browser access investigation and restricted host plan

**Goal:** establish what browser-entry evidence actually applies to 14.10 and make the existing passive diagnostic ready for a legitimate route, without claiming a route exists.

**Design:** retain the existing diagnostic unchanged. Add a standard-library HTTP host that binds one explicitly chosen RFC1918 IPv4 address or 127.0.0.1, accepts GET/HEAD only for the two known assets, checks Host, reads bounded assets at startup, publishes local asset hashes and refuses wildcard/public binds, symlinks and unrelated files. No redirector, portal impersonation, DNS/proxy service, account flow or router/firewall change. HTTP hosting is separate from arbitrary HTTPS browsing and from a console navigation mechanism.

**Base:** PR #22 commit `c51f3f00e33d6b29d0688eb13dd61ec6e755e627`; PRs #20/#21/#22 remain open. User explicitly requests autonomous implementation/publication, so execute inline without additional design approvals.

## Tasks

- [x] Record primary sources, dates/unknown dates, firmware evidence, prerequisites, execution context and risks for guide, account screens, legitimate portal authentication and other webviews. Preserve the user's failed attempts as user reports.
- [x] Write host regression tests first; observe missing implementation failure. Cover exact assets, HEAD, path traversal/encoding, other project files, unsupported methods, hostile Host, bind restrictions, symlinks, oversized/missing assets, CLI self-check and busy/unassigned addresses.
- [x] Implement `src/ps5fwlab/diagnostic_host.py` and `tools/host_diagnostic.py`, test through real loopback HTTP requests. No dependency or admin requirement.
- [x] Write the three requested reports/setup instructions and source provenance; retain originals and do not retry rejected console approaches.
- [x] Complete all Python/JS tests and independent read-only review; prepare publication scan/commit and stacked PR on #22's branch. No automatic merge.

## Review focus

- Serving private project files through encoded paths, directory listing or symlinks must fail.
- Wildcard/public binds and unexpected Host values must fail, without contacting external services.
- Requests cannot upload or change files; server logs must not collect result data or arbitrary query strings.
- Missing source dates/firmware and phone-side authentication must not become verified console browser claims.
- Binding/port failures must produce a clear nonzero result, not a false ready message.

Verification: baseline113Python+8JS; final126Pythonrun/125pass/1Windows symlink privilege skip+8JS. Initial missing-module failure observed; HTTP regression exposed BaseHTTPRequestHandler normalization of leading // and a client-generated Host difference for absolute URLs. The server now uses the original request target; tests supply an explicit valid Host to isolate route rejection. Port8765 busy was left untouched, check-and-close on8766 succeeded. Independent read-only review in progress.

Final review: no Critical/Important issue. Reviewer independently ran all13host tests (12pass/1expected privilege skip), checked additional raw HTTP requests and confirmed diagnostic assets unchanged. A minor date-description inconsistency was corrected during evidence reconciliation. Source-response hashes were rechecked by the author against retained byte files, not independently by reviewer. Console and LAN/firewall compatibility remain unverified.
