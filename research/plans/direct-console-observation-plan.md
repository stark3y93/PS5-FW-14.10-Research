# Proposed direct PS5 observation plan

**Status: NOT APPROVED — PLAN ONLY.** Do not connect to, interact with, or test the physical PS5 until the owner explicitly approves this exact plan. This is a low-risk identification observation, not a vulnerability test. Approval here would authorize only the listed console information screen observation.

## Objective and boundaries

Record the system software version shown by the personally owned PS5 so the research log can distinguish the owner's displayed version from third-party reports. The observation will use the console's built-in Settings UI and manual controller input only. Sony documents the path as **Settings → System → System Software → Console Information**; the screen displays system software version and also exposes network identifiers, which must not be recorded ([Sony support instructions](https://www.playstation.com/en-us/support/hardware/playstation-system-software-application-version/)).

This plan does not test WebKit, JavaScriptCore, kernel interfaces, network services, exploitability, update behavior, or any mitigation. It does not authorize running code, payloads, probes, test pages, homebrew, or diagnostic commands; bypassing a protection; signing in; connecting the console to a network; changing settings; or updating/reinstalling firmware.

## Procedure and data collection

1. The owner confirms that the console is personally owned, powered on normally, and already at the home screen. No network connection is needed.
2. The owner manually opens **Settings → System → System Software → Console Information**.
3. Record only:
   - a local pseudonymous device label chosen by the owner (for example `console-A`);
   - observation date/time in UTC;
   - the exact system software version text visible on screen;
   - whether the same screen displays “Up to date” or another status, if present;
   - optional console family/model group only if the owner wants it recorded and can read it without exposing the serial number.
4. Transcribe the values into a text research log after the owner reviews them. Do not take a screenshot or video under this plan.

Do not record or transmit the console name, IP address, MAC address, serial number, PSN account name/ID, email, network name, DNS/gateway, installed applications, usage history, error history, notifications, or any other screen content. If any such value is visible, leave it out of the notes and do not photograph the screen.

## Rate limits and stopping conditions

- One observation on one day; no polling or repeat measurements.
- Stop immediately if the menu path differs, a login/network/update prompt appears, the console shows unexpected behavior, or any information outside the allowed fields would need to be viewed.
- Do not select update, restart, reset, restore, safe-mode, or network options.
- Manual kill switch: stop controller input, return to the prior screen with the standard back/cancel control, and end the session. If the interface becomes unresponsive, do not continue data collection or issue commands; let the owner decide on ordinary support steps.
- No automated process or cable/network connection is involved, so the owner can stop the observation immediately by putting down the controller.

## Storage and review

Store a short text record in the local research log, not a screenshot. The owner reviews the exact fields before they are added. Keep the pseudonymous label local; do not publish identifying information. Record the method as “manual, built-in Settings UI” and the scope as “displayed version string only.” This observation can confirm what the console reports at that time; it cannot establish firmware binary identity, component versions, patch state, or vulnerability status.

## Approval record

Approval must be an explicit owner message after reviewing this plan. No approval has been recorded.

- Approved scope: ____________________
- Approved device label: ____________________
- Approved date: ____________________
- Owner approval: ____________________

Any change to data fields, procedure, interfaces, or tests requires a new plan and separate explicit approval before execution.
