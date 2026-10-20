# PS5 14.10 FileReader and filesystem-interface follow-up

Date: 20 October 2026. Continues commit `d7f1a7d`; prior [storage/file evidence](PS5_STORAGE_FILE_AUDIT_20261020.md) remains unchanged.

## Live execution and provenance

The authenticated bridge confirmed client `630895e6f5c3` ONLINE immediately before its required code reload. The existing process caches its static assets and task catalog, so an extension could not execute through that unchanged process. Its state was saved to a fresh ignored snapshot and the original append-only log was preserved. Only the same bridge service was restarted, on the same PC address and ports, with a fresh evidence directory; the project was not rebuilt and no dependencies were installed.

After a user-assisted reload/re-pair, session **`a93285a84852`** was ONLINE. Only the new fixed **files** task ran: job **`06a4dcadf071b436`**, completed at **22:12:04.541110 UTC / 23:12:04 BST**, with **13/13 expected rows**. Storage, networking, rendering and previous capability tasks were not repeated on the console.

Context: `http://192.168.4.29:8765`, reported PS5/14.10, AppleWebKit/605.1.15, `isSecureContext=false`. Authentication establishes the bridge session, not cryptographic hardware/firmware identity. [Evidence JSON](PS5_FILE_INTERFACES_EVIDENCE_20261020.json) preserves server snapshots, served-asset hashes and original event records with SHA-256 references. The new source log is `derived/bridge-20261020T221043Z-7328bc/events.ndjson`; automatic task results are at line **4**.

## Three separate access categories

| Category | Conclusion | Evidence and limitation |
| --- | --- | --- |
| Browser-managed data | **PROVEN, within the tested scope** | A 47-byte synthetic in-memory File was read back exactly with FileReader. A synthetic Blob URL was read back exactly by XHR. Previous evidence establishes origin storage readback/persistence/cleanup. No origin-private filesystem directory handle was obtained here. |
| User-selected files | **NOT ESTABLISHED** | Reading the synthetic File did not involve a picker or a user-selected disk file. The gesture-controlled picker and observer controls keep these outcomes separate. No personal file was requested or read by the automatic task. |
| Actual PS5 filesystem directories | **NOT ESTABLISHED** | No native directory handle, actual OS path, directory enumeration or protected file read was obtained. Browser-managed objects and origin storage do not establish OS-directory access. |

## Automatic results

All 13 automatic rows have an empty error string (`""`): no exception was captured. Missing APIs were not deliberately called to manufacture a TypeError. An absent secure-context API on HTTP cannot distinguish an insecure-context restriction from an unsupported implementation; `REQUIRES HTTPS` means a context-controlled retest is required, not a promise of HTTPS support.

| Test | Exact observation | Conclusion |
| --- | --- | --- |
| FileReader synthetic File | `exact_match:true`, `bytes:47`, `expected_bytes:47`, `in_memory_only:true`, `no_user_file_selected:true` | CONFIRMED WORKING: constructor plus `readAsText(file, 'utf-8')`, with exact content comparison |
| Blob/object URL readback | `url_scheme:"blob:"`, `exact_match:true`, `expected_characters:47`, `saved_file_not_inferred:true` | CONFIRMED WORKING: synthetic URL read, then revocation; no saved-file claim |
| `showOpenFilePicker` | `type:"undefined"`, `invoked:false` | Not exposed in this insecure context; HTTPS behavior unknown |
| `showDirectoryPicker` | `type:"undefined"`, `invoked:false` | Not exposed in this insecure context; HTTPS behavior unknown |
| `showSaveFilePicker` | `type:"undefined"`, `invoked:false` | Not exposed in this insecure context; no save picker or write attempted |
| `navigator.storage.getDirectory` | `type:"undefined"`, `invoked:false` | No origin-private directory operation possible here |
| `webkitRequestFileSystem` | `type:"undefined"`, `invoked:false` | Legacy interface unavailable in this context |
| `requestFileSystem` | `type:"undefined"`, `invoked:false` | Unprefixed legacy interface unavailable in this context |
| `FileSystemHandle` | `type:"undefined"`, `invoked:false` | Interface not exposed here |
| `FileSystemFileHandle` | `type:"undefined"`, `invoked:false` | Interface not exposed here |
| `FileSystemDirectoryHandle` | `type:"undefined"`, `invoked:false` | Interface not exposed here |
| Origin-private operation | `invoked:false`, reason `not exposed here; insecure context may be a prerequisite, not proven cause` | Not tested beyond absence; no directory handle obtained |
| Legacy temporary operation | `invoked:false`, reason `legacy temporary filesystem API not exposed` | No callback operation, quota request or directory access performed |

## Bounds and permission handling

FileReader uses the known 47-byte ASCII fixture, one File and one reader, with a 1.5-second deadline and abort on timeout. Readback mismatch is inconclusive. Name/message exceptions from construction, reading and restricted getters are recorded without substituting an unsupported-API claim. The [File API specification](https://www.w3.org/TR/FileAPI/) describes these memory objects and read operations; a synthetic File is not evidence of a selected filesystem file.

Pickers are never called by an automatic task. The new manual button displays an instruction, calls HTML `showPicker()` if available or its normal user-gesture click fallback, and initially records only **REQUIRES USER INTERACTION**. The observer can separately record whether a picker actually appeared, cancellation, no visible result or an error. A reported picker opening is **USER OBSERVATION**, not an automatic file-read success. Save observations cannot establish a picker outcome. Existing upload handling still rejects non-fixture names/sizes before FileReader.

If exposed on a future authorized context, the origin-private check obtains only a bucket-root handle and its kind. The legacy check requests only the temporary namespace with zero requested bytes and checks its root kind. Neither enumerates entries, collects names/paths, creates files, reads existing content or writes user data. These operations did **not** run on this target because their APIs were absent. A storage bucket is defined separately from user directories in the [File System Standard](https://fs.spec.whatwg.org/#dom-storagemanager-getdirectory). The [File System Access draft](https://wicg.github.io/file-system-access/) specifies user activation and permission handling for native pickers; these were not bypassed.

## Blob download versus navigation

The earlier TXT Blob blank page remains historical evidence of an uncertain result. The new automatic Blob read proves the browser can read its own memory URL; it proves neither navigation nor disk saving.

A separate **instrumented HTML Blob control** now allows a user to test navigation. Its download link points at a harmless Blob containing a known heading and one fixed local script. If that document executes with `location.protocol === 'blob:'`, it reports a nonce-bound message back to the opener. The parent accepts only the expected origin, nonce, message marker and protocol. This is direct evidence of controlled Blob-document navigation, not saved-file evidence. A file opened under `file:` cannot report the same success. Missing opener, unsupported script execution, CSP, expired link or no message produces an inconclusive result. The 45-second deadline revokes the URL; it does not infer download success from silence. The HTML control is distinct from the earlier TXT Blob, so its outcome cannot retroactively prove the exact cause of that earlier blank page.

Manual control outcomes are recorded below after user interaction. No save/open outcome is inferred from a click, a returned window, a blank page or a server request.

| Manual control | User observation | Corroborating bridge event | Conclusion |
| --- | --- | --- | --- |
| New file-picker button | “I’m not sure” | None received for `manual.pickerUI` | INCONCLUSIVE: cannot establish activation, visible picker or selected-file read |
| Instrumented Blob control | “I’m not sure” | None received for `manual.blobNavigation`; no validated Blob-page message | INCONCLUSIVE: the navigation hypothesis is not proven for either this control or the earlier blank TXT page |

These replies are preserved separately as conversation-sourced observations in the evidence JSON. They were not inserted as fabricated browser events. No further repeated controller request was made after the uncertain outcomes.

## Verification and final live status

- Python: **136 run, 135 passed, one Windows symlink-privilege skip**.
- JavaScript: **28 passed**: eight passive fixtures, 13 capability fixtures and seven client/observer fixtures.
- New regressions verify exact in-memory readback, readback mismatch, restricted getter exceptions, no automatic picker calls, explicit user-observation classification, rejection of an unrelated save as picker proof, and Blob-versus-file protocol handling.
- Original passive diagnostic assets were preserved. No firmware binaries, credentials or private selected files are included in the report.
- At **22:16:07 UTC / 23:16:07 BST**, client `a93285a84852` was ONLINE; latest heartbeat **22:15:58 UTC**. The single new job was complete. This timestamped observation does not guarantee continued connectivity.

The upgraded LAN bridge remains available for the pending manual observations. The next useful evidence is an unambiguous picker observation and a validated instrumented Blob-page message. HTTPS compatibility requires a separately authorized, already trusted TLS setup; no certificates, permissions or network protections were changed to manufacture that result.
