# PS5 connection and diagnostics proposal

**Status: NOT APPROVED. Preparation only; no console contact under this plan yet.**

This is a separate request from the earlier [manual version-observation plan](direct-console-observation-plan.md). That plan covers only the built-in Console Information screen. It does not authorize a network connection. This proposal expands the possible interaction to Sony's official PS Remote Play client and therefore requires a fresh, explicit owner approval before any console interaction.

## Identity and prerequisite gate

1. The owner identifies the personally owned target by physical possession and a local pseudonym such as `console-A`. Do not use a historical IP address or assume a network responder is the PS5.
2. The owner confirms the Windows PC and that one PS5 are on an existing trusted network. No network or console settings will be changed. If another console could be discovered under the same PlayStation account, stop before launching discovery.
3. The owner reads **Settings → System → System Software → Console Information** and transcribes only the displayed software version and optional “Up to date” status. This screen also displays console name and network identifiers; those are excluded from capture. [Sony version instructions](https://www.playstation.com/en-ca/support/hardware/playstation-system-software-application-version/).
4. The owner reads the current **Settings → System → Remote Play** enabled/disabled state without changing it. If disabled, stop the connection phase and record “not available under unchanged settings.” Sony's official PC instructions require Remote Play to be enabled and the same PlayStation account to be used. [Sony Remote Play instructions](https://www.playstation.com/en-gb/support/games/playstation-remote-play-on-pc-and-mac/).

## Proposed interactions after separate approval

| Step | Exact interaction | Possible effect and risk | Data retained |
|---|---|---|---|
| 1 | Owner manually views the two named Settings screens using the controller. | Other identifiers are visible on Console Information; accidental selection of update or settings controls. | Pseudonym, UTC time, displayed version, current Remote Play enabled state and observation method only. |
| 2 | On Windows, owner opens Sony's official PS Remote Play app and signs in to their own PlayStation account without sharing credentials with this research tool. | Account login may create a normal session with Sony; credentials and account name must not enter logs. | “Official app signed in” yes/no, no account details. |
| 3 | With the one-device prerequisite satisfied, owner selects **PS5** once in the official app. Sony says the app searches consoles associated with the signed-in account and connects automatically. If more than one console appears, stop before selecting one. | App may send discovery and connection traffic, wake/connect to the console, and display its screen. Exact internal discovery packets are not documented here. | Connection success/failure, UTC time, app-reported status, no packet capture or identifiers. |
| 4 | If the app connects, owner visually confirms the target console and immediately disconnects using the app's ordinary controls. | Temporary remote-control session and possible on-screen notification. Avoid controller input to the console. | Confirmation that the official session reached the intended device; no screenshots, audio, video or account information. |

One connection attempt only. There will be no separate port scan, ping sweep, raw protocol request, authentication experiment, manual pairing code, service enumeration or custom network client. If the official app cannot identify the single target without contacting or listing other devices, report the limitation and stop. Manual pairing would establish a device association and needs another separately approved plan.

## Stopping conditions

Stop immediately for any unexpected response, error, prompt for update, sign-in anomaly, additional device, uncertain identity, changed Settings path, request to enable a setting, or request to pair manually. Do not retry automatically. Close the official app and end the session; record only the nonsensitive reason for stopping. Do not alter firmware, settings, storage or network configuration.

## Recording and interpretation

The offline Windows dashboard reads the local SQLite `console_observation` table. It currently shows **not observed** for connection and **unknown** for console-reported firmware. Sony's documentation is displayed separately as documented capability, not as a console observation. After approval, only the fields above will be recorded with their source (`console-reported` or `official-app-reported`), method and time. The generated SQLite database is local and ignored by Git; the catalog and private repository will contain only redacted research conclusions, subject to owner review.

An official Remote Play connection would establish ordinary account-authorized screen access. It would not expose the console's protected files, WebKit/JSC build configuration, firmware binary identity, privilege level or homebrew capability. Those require different authorized evidence and are outside this plan.

## Approval record

- Owner approval for these exact steps: **not received**
- Target pseudonym: **not supplied**
- One-device network/account prerequisite: **not confirmed**
- Date of approved session: **not scheduled**

Do not begin any step involving the physical console or the official app's connection flow until the owner separately approves this plan and the prerequisite gate is satisfied.
