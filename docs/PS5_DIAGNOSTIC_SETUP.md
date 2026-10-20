# Passive diagnostic setup on Windows

**Current status:** the diagnostic has run on the PC, not the PS5. No reliable arbitrary-page entry on PS5 14.10 was found. This host prepares the page; it cannot open a console browser, alter navigation permissions or enable debug options. See the [research result](../reports/PS5_1410_BROWSER_ACCESS.md) and [entry-point evidence](../reports/BROWSER_ENTRYPOINT_EVIDENCE.md).

## 1. Check the restricted host locally

Open an ordinary PowerShell window, without administrator privileges:

```powershell
Set-Location E:\PS5-FW-14.10-Research
python -S tools/host_diagnostic.py --bind 127.0.0.1 --port 8766 --check
```

This prints a JSON manifest containing the URL and SHA-256 values of the two files. `--check` closes the listener immediately; it does not leave a server running. If the port is busy, choose another port above 1023, such as 8767. Do not terminate an existing server or other application merely to free the example port.

Start a PC-only preview:

```powershell
python -S tools/host_diagnostic.py --bind 127.0.0.1 --port 8766
```

Keep PowerShell open and open **http://127.0.0.1:8766/** in Edge. Select **Run passive checks** and verify the completion summary. Stop the server with **Ctrl+C** when done. The page's editable firmware label is not hardware identification; results from Edge remain PC results.

## 2. Prepare trusted LAN hosting only when useful

1. Run `ipconfig` in PowerShell. Find **IPv4 Address** under your active home Wi-Fi/Ethernet adapter. Choose that adapter deliberately; do not use an unrelated VPN/virtual adapter. The host accepts a literal address in `10.x.x.x`, `172.16.x.x`–`172.31.x.x`, or `192.168.x.x`. It does not change your adapter or select one automatically.
2. Replace the example address with that actual PC address:

   ```powershell
   python -S tools/host_diagnostic.py --bind 192.168.1.50 --port 8766 --check
   python -S tools/host_diagnostic.py --bind 192.168.1.50 --port 8766
   ```

3. The printed `url` is the exact LAN URL. The example `192.168.1.50` is not an address discovered on your machine. If the chosen address is not assigned locally, startup fails. The host never silently switches to `0.0.0.0`.
4. A second ordinary PC/phone on the same trusted LAN can test that URL through its normal browser. This tests LAN reachability only; its results are **not PS5 results**. If blocked by firewall, guest isolation or policy, stop here; do not disable security software, alter router isolation or forward ports. The script does not need admin privileges to bind a high port, but cannot guarantee the network permits inbound connections.
5. Stop with Ctrl+C. Anyone with network access to the chosen interface may read the two public files while serving; no passwords/accounts are used. Do not run this on an untrusted public interface. Private-IP validation is not authentication or an audit of existing router configuration.

**Why loopback fails from the console:** `127.0.0.1` always means the device using that address. In the PS5 it refers to the PS5 itself; in Edge on the PC it refers to the PC. The console would need the PC's LAN address **and a working ordinary navigation route**. A LAN URL alone cannot supply that route.

The helper is plain HTTP. Arbitrary HTTPS support, if later demonstrated, does not guarantee HTTP LAN navigation or HTTPS-to-HTTP links work. No TLS interception, untrusted certificate acceptance or certificate installation is required/provided. The raw GitHub source view is not an HTML host, and enabling GitHub Pages would not create a console navigation mechanism.

## 3. Console actions and legitimate authentication

There is no new verified action to perform on your current home connection. Do not resend filtered messages, repeat the YouTube QR flow, unlink services or change DNS/proxy/certificates. The agent has not operated your PS5.

If you are **already legitimately using a network requiring authentication**, consult its operator. A [historical network-operator PS5 guide](https://fcrc.albertahealthservices.ca/chimp/chimp-media-systems-pt-rm-(web).pdf) describes this assisted flow, without a firmware number:

1. Under **Settings → Network → Settings → Set Up Internet Connection**, select the operator-approved network using its supplied credentials.
2. **If offered**, select **How to Authenticate**. If absent, stop and ask the operator; do not force a portal by changing DNS or frequency settings for this research.
3. If the console instructs you to connect a phone/laptop to a temporary PS5 network, use only the network name and passcode shown on your own console. Complete the operator's genuine authentication on the companion device, following its current directions.
4. Return to ordinary console connectivity. Do not publish the passcode, credentials or QR image. This procedure does **not** establish that a webpage ran on the PS5.

This is conditional historical guidance, **not verified firmware 14.10 support**. Do not join or construct a captive network merely to try to unlock browsing. If a genuine console-side webview happens to appear, record its context and whether ordinary external navigation is visibly offered. No route to our page is promised. Portal permissions, client isolation and closing on authentication may prevent any diagnostic run.

## 4. If a future ordinary route reaches the diagnostic

Confirm the page title **Passive browser diagnostic · 1.0**, enter the firmware label you checked separately, and select **Run passive checks**. Photograph the entire summary on the **PS5's display**, including the completion line and UNKNOWN statement. Do not mistake a phone/PC summary for a console result.

Record the exact route, console version, context, displayed page origin and host asset hashes. Keep account names, authentication tokens, passwords and identifiers out of photos. The existing **Select JSON text** button selects text; copy support is not guaranteed. Keep the original photos and any raw JSON; mark manual transcription separately. Exit using the normal screen's Close/Back control. Stop the PC server.

Import a future saved record without changing it:

```powershell
python -S tools/ps5_research.py --browser-diagnostic E:\captures\guide-first.json --target-firmware 14.10 --format markdown --output derived\guide-first-audit.md
```

Use fresh output paths. Capability values and UA strings still cannot prove an exploit, exact engine revision or privileged execution.

## Server guarantees and limits

- Only two fixed regular files are read at startup, each capped at 256 KiB. Existing served bytes remain stable if source files later change; restart to update them.
- Exact routes `/`, `/index.html` and `/diagnostic.js` only. Other files, queries, encoded paths, directory listing, symlink assets and unexpected Host headers are rejected.
- GET/HEAD only; no POST/upload/result endpoint, proxy, redirect, external fetch, DNS service or portal simulator. No routine access/IP/query logging. CSP disables page connections and remote resources; the page remains the passive diagnostic from #22.
- The helper does not open router ports, install packages, change firewall rules or configure the console. It serves HTTP locally until stopped; it is not a production web server or an access-control boundary.

## Run all offline tests

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -S -m unittest discover -s tests -q
node tests/browser_diagnostic.test.cjs
```

The filesystem symlink test can skip on Windows when creating symlinks requires unavailable privileges. No privilege elevation is requested. Other tests exercise real loopback HTTP requests, private bind policy, blocked routes/methods, exact hashes, port conflicts and startup checks. Neither these tests nor the PC preview establish console compatibility.
