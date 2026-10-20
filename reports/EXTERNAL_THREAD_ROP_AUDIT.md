# External thread ROP evidence audit

**Audit snapshot:** external repository commit [`9c89819cf74002b616108bd674b398ae919b40b6`](https://github.com/ZigZagBoi1/PS5-14.10-Research/commit/9c89819cf74002b616108bd674b398ae919b40b6). The complete machine-readable inventory, Git blob IDs, SHA-256 digests, source links, capture links, and selected line evidence are in [external-thread-rop-audit.json](external-thread-rop-audit.json). A SHA-256 binds this audit to a file's bytes; it does not authenticate who captured the file, the console, or its firmware.

The external project's README and probe index report probes 80a–80k as successful. Checking the source against the saved result files narrows that claim substantially:

| Probe | Classification | What the saved record supports |
|---|---|---|
| 80a | PARTIALLY SUPPORTED | Thread-create diagnostics ran. The last section returns an all-ones failure value while the process canary survives; “SECTION COMPLETE” marks the harness path, not a successful thread operation. |
| 80b | PARTIALLY SUPPORTED | Gadget scan found no direct write gadget on the first run. A later stack-canary attempt reports an unchanged marker and explicitly says it was not written. |
| 80c | CONTRADICTED | The log shows the attempted write setup and a readable marker, but it remains `0x41414141`; the log itself says the thread did not write. |
| 80d | CLAIMED BUT NOT DEMONSTRATED | The one saved capture stops after a diagnostic section heading, without a result or completion record. |
| 80e | CLAIMED BUT NOT DEMONSTRATED | A `CS=0x03` sweep line returns zero, but the capture is truncated before the test's full completion/validation output. It does not demonstrate execution of controlled code. |
| 80f | PARTIALLY SUPPORTED | `getcontext` and a process-info query return; the printed labels interpret incorrect offsets as CS/SS. The later full dump shows the actual context fields separately. |
| 80g | CLAIMED BUT NOT DEMONSTRATED | A context based on `getcontext` is modified and thread creation reports success, but binary output interleaves with the result and no controlled side effect or terminal banner is recorded. |
| 80h | CLAIMED BUT NOT DEMONSTRATED | The log records context/register setup and a zero syscall return. It does not show marker readback or a terminal banner; its displayed RDI offset differs from the corrected 80i source. |
| 80i | CLAIMED BUT NOT DEMONSTRATED | Four captures stop at “calling thr_create...”. None includes the source's result section, thread ID, marker readback, completion line, or second-write verification. |
| 80j | VERIFIED FROM RAW EVIDENCE | One complete raw capture logs the `0x41414141` baseline and then `RV=0x0`, `OK=true`, and `M=0xDEADBEEF` with a nonzero thread ID. A different completed run reads back zero and is recorded as a contradiction; other runs are incomplete. All attempts are retained in the JSON inventory. |
| 80k | VERIFIED FROM RAW EVIDENCE | The newer 224016 capture logs the three initial sentinel values, successful return, and all three expected changed values in one result line. The separate final `DONE` banner is absent, but the operation postconditions are present. The older 223328 scan-only capture is not the only available output. |

“Verified from raw evidence” here means the source's expected state transition is present in a saved project capture. For 80j the combined result line is complete; for 80k the complete operation result line is present even though the script's later final banner is missing. The captures are self-published; they have not been independently recorded, hardware identity is unauthenticated, and this audit did not run the Lua. These are reports of **userland thread execution and writes to an allocated userland marker**, not kernel execution, a kernel vulnerability, kernel read/write, hypervisor access, or a jailbreak.

## Provenance and reproducibility

The analyzer walks the external `probes/` and `results/` trees, associates filenames by probe ID, records the Git-commit blob SHA-256, checkout-byte SHA-256, Git blob IDs, and whether text matches after newline normalization. It detects selected terminal/readback patterns, compares the probe index's `OK` claims with the captures, and points to supporting file lines. It stores the external repository commit and creates immutable GitHub blob links. Timestamp-looking filename strings are not authenticated capture times. No external source or log was copied into this repository; only hashes, links, and bounded evidence excerpts are recorded.

Re-run against a local clone:

```powershell
python -S tools/ps5_research.py --probe-audit 'E:\path\to\PS5-14.10-Research' --format markdown --output reports\external-thread-rop-audit.md
python -S tools/ps5_research.py --probe-audit 'E:\path\to\PS5-14.10-Research' --format json --output reports\external-thread-rop-audit.json
```

The tool refuses to overwrite an existing output. The saved JSON included here was generated from commit `9c89819cf74002b616108bd674b398ae919b40b6`.
