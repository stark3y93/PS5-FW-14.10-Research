# PS5 14.10 browser access investigation

> Later user observation (2026-10-20): the passive diagnostic reportedly ran on the real PS5 14.10. The exact entry sequence and raw target JSON remain pending. The historical findings below are preserved; see the [browser bridge status](PS5_1410_BROWSER_BRIDGE.md).

Audit: 20 October 2026. **No reliable, reproducible method to open an arbitrary custom webpage on this 14.10 console was verified.** The diagnostic is ready to serve, but hosting does not supply console navigation. We did not run the diagnostic on the PS5.

## User evidence preserved

The user reports: Sony guide pages open without an address bar or usable external navigation; YouTube displays a device-linking QR code; PlayStation Safety deleted the sent Google URL; the passive diagnostic works in Windows Edge; no PS5 diagnostic run has occurred. These are direct user observations, not independently recorded captures. No attempt was repeated, no messages sent, and no account or console settings changed.

## What the research established

1. [Sony's guide documentation](https://www.playstation.com/en-us/support/hardware/ps5-console-users-guide/) describes page navigation controls without promising arbitrary URL entry. The existing guide is the strongest supported browser surface in the user's current evidence, but it has not met the custom-page goal.
2. The older YouTube tutorial was published in 2022 and last updated in 2024, without naming a tested firmware. The user's QR-only observation prevents treating its account-screen walkthrough as a working route here. [Google's supported sign-in documentation](https://support.google.com/youtube/answer/3015415?hl=en) explains companion-device sign-in, not arbitrary console browsing. Sony ended integrated X/Twitter support in 2023. No account unlink/relink or deceptive flow is recommended.
3. There is primary historical documentation for assisted PS5 network authentication. It does **not** establish a general PS5 browser, current 14.10 portal behavior, or custom-page JavaScript. See the source/firmware/context distinctions in the [entry-point matrix](BROWSER_ENTRYPOINT_EVIDENCE.md).
4. Sony's well-documented public Wi-Fi announcement for **PlayStation Portal** concerns different hardware and companion-device validation. It cannot establish PS5 14.10 functionality.
5. A fixed system status/support/legal screen remains an unverified lead for arbitrary navigation. No exact, non-deceptive supported sequence to the diagnostic was found. No cross-site navigation assumption was inferred from a desktop copy of a Sony page.

Sources and original-publication-date limitations are recorded individually in [BROWSER_ACCESS_SOURCE_PROVENANCE.json](BROWSER_ACCESS_SOURCE_PROVENANCE.json). Ten source responses were retained locally with SHA-256; vendor/network-operator documents are preferred over recycled tutorials. Search queries included exact firmware plus browser, captive portal and authentication terms. No independent 14.10 capture meeting the navigation/JavaScript criteria was located. This does not establish that captive portals were removed or that browsing is impossible in every context.

## Captive portals: three different outcomes

| Outcome | What it establishes | Can it run our diagnostic on the PS5? |
|---|---|---|
| A phone/laptop completes network authentication for the console | The console may gain network access. | **No evidence of console page execution.** Running the page on the phone still measures the phone. |
| The console displays a restricted operator authentication page | At most, one portal page is reachable in that context. | **Unknown.** External links, HTTP/HTTPS navigation, LAN access and JavaScript can be restricted separately. |
| A custom page actually completes on the console | A specific ordinary page and JS are reachable on the identified device. | **Yes for that recorded context**, if both diagnostic files load; no such 14.10 record exists here. |

Legitimate portals authenticate users on networks they are entitled to use. They are not DNS hijacks of Sony's HTTPS guide. This audit does not create an artificial portal, inspect credentials, intercept TLS or change network configuration. Even an allowed HTTPS navigation route might block the helper's plain HTTP LAN URL; the host intentionally adds no certificates or TLS bypass. Guest Wi-Fi can also isolate clients from the PC.

## What to do on the PS5 now

On your existing home connection there is **no newly verified navigation sequence to follow**. Do not repeat the guide, YouTube or message attempts merely because a PC server prints a URL. Prepare the PC host using [PS5_DIAGNOSTIC_SETUP.md](../docs/PS5_DIAGNOSTIC_SETUP.md); continue ordinary console use until new route evidence appears.

Only if you are independently using an authorized network that genuinely requires authentication, follow its operator's current instructions and the console's own prompts. The historical assisted procedure and stop conditions are documented in the setup guide. That is a network-connectivity procedure, not a recommendation to move networks for this experiment. If authentication occurs on your phone, it does not advance PS5 diagnostic execution.

## Useful PC-side result

`tools/host_diagnostic.py` serves exactly `/`, `/index.html` and `/diagnostic.js` from two bounded, hashed startup snapshots. It defaults to PC-only loopback and accepts an explicit chosen RFC1918 IPv4 address for trusted LAN use. It refuses wildcard/public binds, directory listing, traversal, unrelated project files, uploads and unexpected Host values. No administrator command, dependency installation, firewall rule, router port, DNS/proxy change or external upload is performed. `--check` validates the bind and closes without serving. A bind failure is a failure, never a fallback to all interfaces.

The server exposes only the public diagnostic assets and has no authentication; trusted LAN peers may read them while it runs. The passive page itself is unchanged. Windows firewall or network policy may block inbound LAN access even when local startup succeeds. Do not disable protections to make it work. More details and exact PowerShell commands are in the [setup guide](../docs/PS5_DIAGNOSTIC_SETUP.md).

## Next evidence worth collecting

Prioritize an independently retained **14.10 ordinary-navigation record** with the full route and execution context, or an authoritative vendor/network-operator confirmation of console-side portal/browser behavior. A guide screenshot without an external route, another PC pass, or a companion-device login cannot substitute. Firmware/source research can continue offline while browser access remains unresolved.
