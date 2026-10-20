# Passive PS5 browser diagnostic

**Browser-access follow-up:** the user has now reported no external guide route, QR-only YouTube linking and Safety deletion of a message URL. Do not repeat these attempts without new evidence. No arbitrary-page method was verified. Prefer the new [restricted host/setup guide](../docs/PS5_DIAGNOSTIC_SETUP.md); [entry-point evidence](BROWSER_ENTRYPOINT_EVIDENCE.md) distinguishes historical assisted authentication from console-side execution. The original Phase 4 instructions below remain preserved as conditional context, not a verified route.

The files in [`diagnostics/browser`](../diagnostics/browser/) perform bounded **API availability checks**. They do not construct/load a FontFace, override iterators, allocate test buffers, compile dynamic JavaScript, invoke native interfaces or run an exploit. Ordinary JavaScript/CSS operations still depend on the browser functioning correctly; this is designed as a harmless page, not a guarantee against every browser defect. It was tested on a PC and with isolated JavaScript fixtures, **not on a PS5**.

## First establish whether navigation is available

[Sony documents](https://www.playstation.com/en-us/support/hardware/ps5-console-users-guide/) this path:

1. From the PS5 home screen, open **Settings → User's Guide, Health and Safety, and Other Information → User's Guide**.
2. Use the directional buttons to move focus, Cross to select and the right stick to scroll. Circle goes back. Options → Close exits the guide.
3. Record whether the guide exposes an ordinary external link/navigation route. A guide that opens successfully does **not** mean you can type a custom URL.
4. If no ordinary route lets you reach a URL you control, **stop the console portion here**. Photograph the guide's visible controls and record the console version separately. The PC alternative below still works.

This investigation found no vendor-supported method to enter an arbitrary URL in the 14.10 guide. Sony's [launch FAQ](https://blog.playstation.com/2020/11/09/ps5-the-ultimate-faq/) says there is no dedicated browser app; that historical statement is not proof of today's link restrictions. Message links, account-link flows and USB HTML execution were not verified. No specific chain of guide links to a custom URL is asserted. Do not change DNS, proxy settings, certificates, sign-in flows or the console firmware for this diagnostic. DNS cannot by itself satisfy an HTTPS server's certificate identity. GitHub Pages hosting, even if separately enabled, does not create a navigation route from the guide.

## PC preview — works without console navigation

Open PowerShell on the PC:

```powershell
Set-Location E:\PS5-FW-14.10-Research
python -S -m http.server 8765 --bind 127.0.0.1 --directory diagnostics/browser
```

Keep that window open. In the PC browser open **http://127.0.0.1:8765/**. Select **Run passive checks**. You should see **PASSIVE CHECKS COMPLETE**, a summary and JSON. The initial firmware label is merely editable text; PC results remain PC results even if it says 14.10. Close the page and press **Ctrl+C** in PowerShell to stop serving.

The server exposes only the diagnostic folder. It does not collect results; standard HTTP access logging can record requesting addresses and file requests locally. The page itself has no result upload, beacon, cookies, storage, location/address collection, external resources or clipboard-read operation. Results remain on screen. CSP disables network connections and remote font/media/object loads. The two same-origin static files must be served together; GitHub's raw file view is not a webpage host.

## Conditional PS5 run — only if a normal external route already exists

1. On the PC run `ipconfig` and note the **IPv4 Address** of the active adapter on your trusted home LAN. Do not publish this address with your results.
2. Start the same static folder server bound to that exact address, replacing the example:

   ```powershell
   python -S -m http.server 8765 --bind YOUR_PC_LAN_IPV4 --directory diagnostics/browser
   ```

3. From an ordinary allowed link/navigation route on the console, open `http://YOUR_PC_LAN_IPV4:8765/`. **This step is conditional, not a verified 14.10 guide feature.** Loopback `127.0.0.1` on the PS5 would refer to the PS5, not the PC. HTTPS-only/mixed-content rules, LAN isolation or the PC firewall may prevent access. Do not disable protections or create router port forwards; if blocked, stop and use the PC alternative.
4. Confirm the title **Passive browser diagnostic · 1.0**. Enter the firmware label you read from the console's system information. Select **Run passive checks** with Cross. Wait for the completion message.
5. Photograph the complete summary, including the final UNKNOWN statement. Scroll to capture every line if needed. Keep any account names or personal notifications out of photos. Record how you reached the page and whether it was a guide, account dialog or another context; contexts can differ.
6. If text selection/copy works, select **Select JSON text**, copy through the browser's normal controls and transfer the text to a new local file. This button selects; it does not promise clipboard access or a file-download feature. Otherwise transcribe carefully to a new file using the schema example and mark it as a transcription in a separate note. Preserve photographs separately as the originals.
7. Exit with Options → Close, or Circle. Stop the PC server with Ctrl+C.

No console operation was performed by the agent. A missing/false API value can mean a restricted context or implementation difference; a true value cannot identify the patch state. `cssFontFamily` checks CSS syntax support; `FontFace` and `fontSet` check availability without creating/loading fonts. `secureContext` describes the page's security context, not console security. The timestamp is the browser's clock, not an authenticated capture time.

## Analyze saved JSON offline

Choose fresh filenames; original inputs and existing output files are never overwritten:

```powershell
python -S tools/ps5_research.py --browser-diagnostic E:\captures\guide-first.json --target-firmware 14.10 --format markdown --output derived\guide-audit-first.md
python -S tools/ps5_research.py --browser-diagnostic E:\captures\guide-first.json E:\captures\guide-second.json --target-firmware 14.10 --format json --output derived\guide-comparison-first.json
```

The importer stores exact-byte SHA-256, input filenames and JSON pointers, marks incomplete/invalid records, excludes mismatched labels/UAs and duplicate content from comparison, and reports differing Boolean observations. A PS5-looking UA is only a consistency check. It cannot authenticate hardware, an executable, a memory fault or privileged execution. Unsupported extra claim fields are flagged and ignored. [Synthetic examples](../research/examples/browser/README.md) can exercise this workflow immediately without a console. Keep real captures local until reviewed for private information.

If no external navigation route exists, the highest-value alternative is the authorized source/build correspondence investigation in [NEXT_RESEARCH_STEPS.md](NEXT_RESEARCH_STEPS.md). Running the PC page validates the diagnostic, not the PS5's engine.
