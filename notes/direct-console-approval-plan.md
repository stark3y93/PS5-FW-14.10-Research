# Separate proposed direct-console observation plan — approval required

**Status:** proposal only. No console contact or test is authorized by this document.

1. **Owner confirmation and preparation.** The owner confirms physical possession, current firmware version, and that a local display/controller session is available. Record only the date, firmware version string shown by Settings, and console model family. Risk: accidental disclosure of account details in photos. Keep account names and identifiers out of notes.
2. **Interaction proposed:** use the controller and display to open **Settings → System → System Software → Console Information** and manually transcribe the displayed system software version. Do not browse external pages, attach USB media, enable debug settings, or alter any setting. Data collected: version/build text only. Risk: minimal normal UI interaction; stop if the menu differs or requires a sign-in/update.
3. **Optional later interaction, requiring separate approval:** view a locally hosted, static diagnostic page containing no JavaScript, form, redirects, downloads, or network requests beyond the page fetch. Data would be a user-agent string and whether the page renders. Risk: connecting a console browser to a local service; stop on any unexpected request, prompt, crash, or network destination. This optional step is not part of the initial approval request.

**Stopping conditions:** any unexpected system prompt, software-update request, crash, account/personal-data display, change in network destination, or uncertainty about the next interaction. The manual kill switch is to close the menu or browser with the controller and disconnect the PC-hosted service. No payloads, fuzzing, repeated requests, protection bypasses, firmware changes, or exploit tests are proposed.

Approval must name the exact step(s). Until then, all work remains PC-only.
