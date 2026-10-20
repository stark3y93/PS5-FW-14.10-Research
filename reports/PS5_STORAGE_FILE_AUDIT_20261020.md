# Live PS5 14.10 storage and file audit — 20 October 2026

## Scope and live connection

This audit reused the existing authenticated bridge at `http://192.168.4.29:8765`. No server restart, PS5 setting change, permissions bypass, exploit, protected-storage access or user-file deletion was performed. The account/firmware identity is user-supplied and browser-reported, not hardware-attested.

At the first authenticated check, server time **21:53:44 UTC / 22:53:44 BST**, the requested client `7243d0ad563b` was **OFFLINE**; its last heartbeat was **21:49:34 UTC**. Its earlier completed tests were not treated as live execution.

After the user replied “page open,” a newly paired session **`3d699bb03ce4`** was ONLINE. Its registration was recorded at **21:54:29 UTC**. The audit scheduled these tasks specifically on that new session:

| Task | Job | Result time UTC | Evidence |
| --- | --- | --- | --- |
| storage | `fbed8624f915d6c4` | 21:55:11.823377 | Original `events.ndjson`, line 18 |
| surface | `5165048c10437b8a` | 21:55:25.784581 | Original `events.ndjson`, line 20 |
| security | `4b06b4ad8f8e584d` | 21:55:45.978805 | Original `events.ndjson`, line 22 |
| storage after requested reload/re-pair, client `028819fe310b` | `dc1b661d1c6bf332` | 22:00:00.127952 | Original `events.ndjson`, line 27 |

All four jobs completed with the full expected result sets: **41 automatic result rows**, plus a separate successful owned-storage cleanup event. These are normal-webpage capability checks, not vulnerability tests. No JavaScript or arbitrary commands were injected through the bridge.

Context: reported PlayStation 5 / **14.10**, AppleWebKit/**605.1.15**, Version/17.0 Safari/605.1.15; origin `http://192.168.4.29:8765`; `isSecureContext=false`; `crossOriginIsolated=false`. These compatibility tokens do not identify an exact engine source revision. Results below are scoped to this page/context.

## Evidence matrix

“CONFIRMED BLOCKED” below also includes an API observed absent in this context. It does not identify the cause, prove a firmware-wide policy or predict HTTPS behavior. A blank error field means no exception was captured; an error must not be invented to explain absence.

| Capability | Classification | Exact observation / error | Evidence and confidence |
| --- | --- | --- | --- |
| localStorage write/read | CONFIRMED WORKING | `readback:true`, `prior_page_sentinel:true`; error `""` | line 18, `storage.local`; automated, medium |
| sessionStorage write/read | CONFIRMED WORKING | `readback:true`, `prior_page_sentinel:true`; error `""` | line 18, `storage.session`; automated, medium |
| Persistence across page instances | CONFIRMED WORKING | `prior_page_sentinel_seen:true`, `stores_with_prior_marker:2`; error `""` | line 18, `storage.reload`; automated, medium |
| Persistence after requested ordinary reload/re-pair | CONFIRMED WORKING, user-assisted | After the explicit reload instruction, user replied “re connected”; new session `028819fe310b` found both prior-page markers (`prior_page_sentinel:true`, stores 2). The exact UI transition is user-reported, not independently traced. | lines 24/27 plus controller reply; medium for persistence, low for exact UI transition |
| Temporary localStorage write/read/remove | CONFIRMED WORKING, limited | 2,048 ASCII characters, maximum UTF-16 payload 4,096 bytes. Code removes the temporary key in `finally`; no independent null readback follows deletion. | line 18, `storage.estimate`; automatic operation evidence, medium; deletion readback unverified |
| localStorage/sessionStorage marker deletion | CONFIRMED WORKING, limited | Cleanup returned `removed:2`, `preserved_collisions:0`, `errors:[]`; error `""`. Both owned markers were removed through `removeItem` calls without an exception. No separate post-delete null readback was captured. | line 28, `manual.storageCleanup`; automated, medium |
| IndexedDB | CONFIRMED BLOCKED | `observed:false`; error `""`. The client returns false when `window.indexedDB` is absent; no open/transaction exception was captured. | line 18, `storage.indexedDB`; automated, medium; cause unknown |
| Quota estimate API | CONFIRMED BLOCKED | `estimate_available:false`; error `""`. The successful combined storage row proves the small temporary operation, **not** availability of a quota estimate or an actual quota size. | line 18, `storage.estimate`; automated, medium |
| File / FileReader / Blob / FileList / object-URL API exposure | CONFIRMED WORKING, presence only | All five recorded as true; error `""`. No File constructor or synthetic FileReader readback was executed by this task. | line 20, `surface.fileAPIs`; automated, medium |
| Blob creation and object URL used by worker | CONFIRMED WORKING | `security.worker:true`; error `""`. Code creates a tiny Blob/object URL, receives the expected worker marker, terminates the worker and revokes its URL. | line 22, `security.worker`; automated operation evidence, medium |
| File input element | CONFIRMED WORKING, presence only | `surface.fileInput:true`; error `""`. This is not proof of a functioning picker. | line 20; automated, medium |
| Picker UI | INCONCLUSIVE | User replied “think i didi it,” then “I’m not sure”; no definite visible outcome or selected-file callback established. | User reply; low / awaiting clarification |
| Read user-selected synthetic file | REQUIRES USER INTERACTION | No validated synthetic file selection/read result. Picker outcome is uncertain and no saved synthetic fixture was established. No personal file was requested. | No `manual.fileUpload` success; low |
| TXT download save | INCONCLUSIVE | Initial observation: “nothing json fills at the bottom.” Exact-link retest: “download tiny text pressed nothing happened.” No visible save/open or explicit error. A page JSON update is local logging, not download proof. | Exact attachment-click events at lines 29/30 plus user observation; low for save outcome |
| HTML download attribute honored | REQUIRES USER INTERACTION | Earlier client recorded a link request only. No save/inline outcome confirmation. | Historical line 14; low |
| Blob creation through manual control | CONFIRMED WORKING | `Blob URL created; click its link, then report observed outcome`; error `""`. Separate from the automatic Blob-backed worker test. | line 31, `manual.blobDownload`; automatic operation observation, medium |
| Blob download save | INCONCLUSIVE | Retest recorded `Blob URL created and link clicked; confirm actual outcome below`; user then confirmed a separate **Blank page**. No saved-file or synthetic-content readback; no exact error supplied. | line 32 plus user observation; low for save outcome |
| Reopen downloaded file in supported UI | REQUIRES USER INTERACTION | No saved file or supported download/open UI established; testing is blocked by the missing saved-file prerequisite. A webpage cannot directly inspect a download directory. | Manual gate only; low |
| `showOpenFilePicker` | CONFIRMED BLOCKED in this HTTP context | `surface.fileSystem:false`, gate `REQUIRES HTTPS`, error `""`. HTTPS is untested and is not guaranteed to expose it. | line 20; automatic exposure check, medium; cause not isolated |
| Directory picker, directory enumeration and origin-private filesystem | INCONCLUSIVE | Existing fixed suite does not separately test `showDirectoryPicker`, legacy filesystem APIs or `navigator.storage.getDirectory`. No directory was enumerated. | Explicit coverage gap; no target claim |
| Actual filesystem path disclosure | INCONCLUSIVE | No actual filesystem path captured. Existing upload control deliberately does not collect paths. Filenames, fakepath strings, Blob URLs and HTTP URLs are not evidence of a PS5 OS path. | No path evidence; low |

## Access to PS5 internal files

**NOT ESTABLISHED.** Origin-scoped storage and Blob-backed script execution do not demonstrate access to protected PS5 files, installed titles, saves or operating-system directories. No internal path, arbitrary file read or directory listing was obtained. This audit does not claim an exhaustive proof that every browser filesystem interface is absent.

The [File API](https://www.w3.org/TR/FileAPI/#file-section) specifies that `File.name` lacks path information. The [HTML file-input specification](https://html.spec.whatwg.org/multipage/input.html#file-upload-state-(type=file)) documents the synthetic `C:\fakepath\` value; it must not be promoted to an actual path. The [File System Standard](https://fs.spec.whatwg.org/#dom-storagemanager-getdirectory) distinguishes access to a site's storage bucket filesystem; even success there would require separate evidence before claiming OS/user-directory access.

## Reproduction and evidence preservation

The original append-only evidence is `derived/bridge-20261020T214316Z-e5aedd/events.ndjson`. [The credential-free audit evidence](PS5_STORAGE_FILE_EVIDENCE_20261020.json) preserves the original-client history, first authenticated offline observation and new-client events with original line numbers and SHA-256 values including each event's newline. The source file is live and may grow; its historical whole-file hash describes only the specified captured prefix/snapshot. Original logs and timestamped bridge snapshots remain untouched.

The source implementation is [suite.js](../diagnostics/bridge/suite.js): `sentinel` and `database` implement storage checks; the `storage` task defines the temporary quota operation and prior-page marker logic; the `surface` task reads API exposure; `worker` creates/revokes its Blob URL. The client [manual controls](../diagnostics/bridge/client.js) require gestures and validate only the known 47-byte synthetic TXT. The server [task catalog and validation](../src/ps5fwlab/bridge.py) accepts only fixed tasks. These source references explain what the recorded operations can and cannot establish.

Pending controller-dependent outcomes must be appended with their source and observed result; do not replace them with a presumed success or block. The current suite has no remote custom-instruction channel. Instructions therefore use its existing visible local controls and the chat; none was falsely claimed to have been pushed onto the PS5 screen.

## Final status and next bounded checks

At **22:02:46 UTC / 23:02:46 BST**, all three recorded sessions were OFFLINE by the bridge's 30-second rule. The newest session's last heartbeat was **22:01:38 UTC**. This was checked after the Blob link had opened another page. Background-page suspension is a possible explanation, not an established cause. The four completed jobs and recorded cleanup are past execution evidence; the console is not claimed to remain live.

A later new session **`630895e6f5c3`** reconnected. At the final authenticated check, **22:04:09 UTC / 23:04:09 BST**, it was **ONLINE**, last heartbeat **22:04:07 UTC**; the three earlier sessions remained OFFLINE. No additional storage write was scheduled on this newest session, preserving the completed cleanup. Both status snapshots are retained in the evidence JSON so the earlier offline state is not presented as current.

Raw automatic gates: **26 available, eight blocked/unavailable, five requiring HTTPS and two requiring user interaction** across 41 observations. These are not 41 successful capability tests. The combined `storage.estimate` row's availability must not be misreported as a successful quota estimate.

Remaining useful checks require additions to the fixed allowlist and a deliberate service/client update: a tiny in-memory File/Blob/FileReader roundtrip; independent post-delete null readback; separate quota-interface exposure checks; and presence checks for directory/legacy/origin-private filesystem interfaces. The running server caches its allowlist and assets, so silently editing source files cannot make those tests execute on the existing client. No arbitrary evaluation endpoint or hidden permission prompt was added to get around that constraint. User-selected-file reading and downloaded-file reopening remain unverified because neither a functioning picker nor a saved synthetic fixture was established. No personal file should be substituted to fill the evidence gap.


## Attribution and coverage cautions

The first new click event (line 23) is `manual.downloadLink`, which identifies **Open synthetic TXT**, not the attachment link. No matching Blob-download event accompanied the initial blank-page report. Consequently those reports cannot independently authenticate which exact control ran. An exact attachment-link retest was requested and its outcome is preserved separately. No click/request is classified as a saved download.

The user identifies the console address as `192.168.4.30`; the bridge reports page origin, user agent and session heartbeats, but its saved registration does not bind the session to an independently authenticated hardware identity.
