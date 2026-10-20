# PS5 14.10 browser research bridge

This collects ordinary webpage observations on your trusted LAN. It cannot enable debug options, kernel access, sandbox escape, internal storage access or a jailbreak. The original passive diagnostic files are unchanged and are also served at `/passive/`.

## Start on the PC

No installation or administrator rights are required. In PowerShell:

```powershell
Set-Location E:\PS5-FW-14.10-Research
# Validate the assets and two unused ports without starting a persistent server.
python -S tools/ps5_bridge.py --bind 192.168.4.29 --port 8768 --secondary-port 8769 --check
```

The already working diagnostic uses port 8765. To reuse that same URL, **you** must stop its existing hosting command with Ctrl+C in its own terminal, then run:

```powershell
python -S tools/ps5_bridge.py --bind 192.168.4.29 --port 8765 --secondary-port 8766
```

The bridge does not stop another server. If either port is occupied it exits with a clear error. If you can navigate to a different URL on the PS5, you may instead run the bridge on 8768/8769 and leave the original server running.

Keep the printed pairing key and separate dashboard key local. On the **PC**, open [the dashboard](http://192.168.4.29:8765/dashboard) and enter the dashboard key. Use the bound LAN address for this dashboard; its PC-address restriction will reject other LAN clients. HTTP credentials and results are not encrypted: use a trusted LAN with no port forwarding. No firewall, router, DNS, proxy or certificate settings are changed by this tool.

`127.0.0.1` always means the device opening the URL. On the PS5 it points back to the PS5, not your PC. Use `192.168.4.29` while that remains your PC's LAN address. A changed address, guest-network isolation, Windows Firewall or an occupied port can prevent connectivity; the suite does not bypass these restrictions.

## Connect the real PS5

1. Use the same navigation route that already worked for you to open `http://192.168.4.29:8765/`. The exact navigation route has not been supplied to this repository; no new entry method is claimed.
2. Reload so the new **PS5 browser research bridge** page appears. Enter the printed **pairing** key and keep the firmware label at `14.10`. Click **Pair and enable scheduled tests**.
3. For a new baseline, run **surface** first. For the file-interface follow-up, run only **files**; earlier completed categories need not be repeated. Check the PC dashboard for the client and uploaded rows. The firmware label and user agent are self-reported, not cryptographic proof of firmware identity.
4. Run **storage**, **network**, **security**, then **rendering**, one category at a time. The dashboard can schedule these same five fixed tasks after pairing. It cannot supply JavaScript, commands, target URLs or exploit payloads.
5. For persistence, run storage, use normal browser Reload, pair again, then run storage again. Only a marker from a different page instance is persistence evidence. Session storage survives same-tab reload where supported, not necessarily closing the tab or console restart. Origin changes, including HTTP to HTTPS, use different storage.
6. Complete the manual tests below if desired. Finally click **Remove suite-owned storage sentinels**. Export JSON and Markdown from the PC dashboard.

Pairing explicitly enables the five bounded tasks, including their synthetic storage and rendering operations. Downloads, file selection, popups and navigation require separate PS5 gestures. The suite never reads the clipboard or asks for hardware/location permission. The Permissions query checks a state; it does not request a position.

## Download and file checks

All generated files contain exactly 47 ASCII bytes:

```text
PS5 capability suite: harmless synthetic text.
```

The final newline is included. Check the ordinary link, attachment download, `download` attribute with an inline response, and Blob URL separately. Creating a Blob, clicking a link or receiving a server request **does not prove that a download was saved**. Record the actual visible outcome using the test/observation controls. If there is no visible result, use that observation; do not call it a confirmed block without an explicit indication.

Only use a normal download/open UI if one exists. A webpage cannot inspect the PS5 download directory. The initial file-open row therefore says **NOT TESTABLE FROM A NORMAL WEBPAGE**; a subsequent manual observation can describe what you personally opened. Do not browse or select personal files.

The optional upload input accepts only a user-selected file with the exact generated name (`ps5-synthetic.txt`, `ps5-attribute.txt` or `ps5-blob.txt`) and 47-byte size, then verifies the exact synthetic content locally. Renamed duplicates such as `(1)` are rejected. No file content or name is uploaded; only the validation outcome is recorded. A matching name and size cannot authenticate content before reading, so select only a file you know this suite generated.

## What the gates mean

| Gate | Interpretation |
| --- | --- |
| CONFIRMED AVAILABLE | The stated operation or presence check succeeded in this recorded page/context. Presence alone does not prove unrestricted use. |
| CONFIRMED BLOCKED OR UNAVAILABLE | The recorded property was absent or a specific restriction was observed here. It is not a console-wide verdict. The controlled CORS denial is expected. |
| INCONCLUSIVE | Error, timeout, missing control, mixed results or insufficient observation; cause not established. |
| REQUIRES HTTPS | A secure-context prerequisite prevents the relevant conclusion here; HTTPS is a retest requirement, not a guarantee of support. |
| REQUIRES USER INTERACTION | A gesture, reload or visible outcome must still be supplied. |
| NOT TESTABLE FROM A NORMAL WEBPAGE | A normal webpage has no direct facility to establish this, such as inspecting an internal downloads directory. |

Every uploaded row includes the canonical expected operation, observed value, error, page scope, server-observed origin/transport, method/confidence and append-only evidence reference. Automated availability/block observations have MEDIUM confidence; manual observations and unresolved conditions have LOW confidence. These are evidence quality labels, not exploit severity.

## Network and HTTPS interpretation

The secondary port is a second controlled origin. The CORS test first reads an explicitly allowed response, then checks that the no-allow-header response is unreadable. Failure of the positive control is inconclusive. Other tests check fetch/XHR GET and POST, one authenticated synthetic WebSocket echo, one EventSource event, a tiny response stream, a controlled delayed response and a controlled connection close. Timeout/failure checks require a successful same-origin XHR control.

On non-loopback HTTP, secure-context APIs may be absent. Loopback HTTP can be considered trustworthy, so PC loopback results cannot stand in for PS5 LAN results. See the [Secure Contexts specification](https://www.w3.org/TR/secure-contexts/). WebAssembly absence on HTTP is recorded for that context; neither permanent disablement nor successful support over HTTPS follows from it. The suite validates an eight-byte empty module where supported and does not instantiate it; see the [WebAssembly JavaScript API](https://webassembly.github.io/spec/js-api/).

Optional TLS accepts an **existing**, appropriately trusted certificate and private key:

```powershell
python -S tools/ps5_bridge.py --bind 192.168.4.29 --port 8775 --secondary-port 8776 --tls-cert C:\path\to\existing-cert.pem --tls-key C:\path\to\existing-key.pem
```

The certificate must be valid for the bound IP and already trusted by the client. The tool does not create certificates, install trust, disable verification or instruct you to bypass warnings. If such a certificate is unavailable, leave the HTTPS comparison untested. TLS on the PS5 has not been verified. The suite does not request cross-origin isolation headers, so a false isolation flag or absent SharedArrayBuffer describes this page's policy as well as browser availability.

## Bounds, failures and evidence

- One active task per client, six fixed categories including the bounded **files** follow-up; 60-second server job deadline and 30-second client warning. Missing expected rows mark a job partial, not completed evidence.
- Heartbeats every 10 seconds; ONLINE means a heartbeat within 30 seconds, not independently verified console power status. Browser suspension can cause OFFLINE.
- At most eight paired clients and 128 jobs per server run, 2,048 result rows, 64 rows per request, 64 KiB request bodies and 32 MiB evidence/snapshot output. Restart for a fresh run after reaching limits. Reloading and re-pairing consumes a client slot.
- A single 256 KiB typed-array allocation, 16×16 canvas/WebGL surfaces, 10,000 additions, one tiny worker, and synthetic storage writes only. The temporary quota write has at most 4 KiB UTF-16 payload; this is not quota exhaustion or a memory stress test.
- The service worker has no fetch handler or cache and is unregistered after the test. If unregister fails, the row is inconclusive. Storage cleanup preserves unexpected values at suite-owned keys and reports collisions.
- Results remain in the page's raw-text area before upload. Keep that text if an upload fails. Control transport requires XMLHttpRequest; the unchanged passive page remains available if bridge pairing cannot work.

Each server start creates a new ignored `derived/bridge-<UTC>-<random>/` directory. `events.ndjson` contains timestamped events; result references include its line number and the SHA-256 of that exact event line. Snapshot exports create new JSON/Markdown files without overwriting prior results. Client/server asset hashes accompany snapshots. Pairing/session/dashboard credentials are held in memory and excluded from evidence and exports. Reports can contain user agents, browser observations and origins: review before sharing. This tool does not prove firmware authenticity or establish a vulnerability.

Stop with Ctrl+C when finished. To restore the original root page after using 8765:

```powershell
python -S tools/host_diagnostic.py --bind 192.168.4.29 --port 8765
```

## Local tests

```powershell
Set-Location E:\PS5-FW-14.10-Research
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -S -m unittest discover -s tests -v
node tests/browser_diagnostic.test.cjs
node tests/bridge_suite.test.cjs
node tests/bridge_client.test.cjs
```

Python uses only its standard library. Node tests use built-in modules with synthetic browser fixtures; no package installation is needed. Loopback HTTP integration tests start temporary PC-only listeners, never connect to a PS5 and never scan the LAN.
