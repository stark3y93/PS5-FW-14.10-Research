# Probe 80i–80k verification

Audited external snapshot: `ZigZagBoi1/PS5-14.10-Research` at commit [`9c89819cf74002b616108bd674b398ae919b40b6`](https://github.com/ZigZagBoi1/PS5-14.10-Research/commit/9c89819cf74002b616108bd674b398ae919b40b6). This is a static comparison of published Lua source and self-published text captures. No probe was executed.

## 80i: controlled write claim

The source initializes an allocated marker to `0x41414141`, configures the thread context, requests thread creation, then intends to print the thread ID, marker value, repeat-write result, process canary, and `PROBE 80i COMPLETE`. This gives clear, falsifiable expected observations.

The four public captures are:

| Capture | SHA-256 | Saved ending |
|---|---|---|
| [221559](https://github.com/ZigZagBoi1/PS5-14.10-Research/blob/9c89819cf74002b616108bd674b398ae919b40b6/results/phase17_new_vectors/80i_thread_write_final_20261019_221559.txt) | `febb351273fe5c93c270458810de7079cf8034827abd8deb4503090ed6a4df90` | Ends at the call to `thr_create`. |
| [221625](https://github.com/ZigZagBoi1/PS5-14.10-Research/blob/9c89819cf74002b616108bd674b398ae919b40b6/results/phase17_new_vectors/80i_thread_write_final_20261019_221625.txt) | `f71921384c8672f303aa072bf93b8740c3ba15e111d54db4cc91f799b8e948df` | Ends at the call to `thr_create`. |
| [221714](https://github.com/ZigZagBoi1/PS5-14.10-Research/blob/9c89819cf74002b616108bd674b398ae919b40b6/results/phase17_new_vectors/80i_thread_write_final_20261019_221714.txt) | `4e22bf6dfe0413d0d43b11b3828cf6c869cc7549bb6307d7a8c0eb3bf66ee929` | Ends at the call, followed by a few corrupted/non-result bytes. |
| [221733](https://github.com/ZigZagBoi1/PS5-14.10-Research/blob/9c89819cf74002b616108bd674b398ae919b40b6/results/phase17_new_vectors/80i_thread_write_final_20261019_221733.txt) | `c907ff22e4291ad7e287576c1abc247d6b454b9a7146d9c64f62eb8c418e03ec` | Ends at the call to `thr_create`. |

None records the original marker value in the result, the expected `0xDEADBEEF` readback, the second write, restoration, or the completion print. This is **CLAIMED BUT NOT DEMONSTRATED**, not a verified 80i write. The lack of post-call output cannot distinguish a thread failure, process termination, buffering, or capture truncation. It does not identify a crash cause. Since this source writes only to a new scratch allocation, restoration of pre-existing application data is not applicable; a robust proof should still show a before value, intended readback, and (if safe and intended) a restored scratch value.

Source SHA-256 (Git commit blob bytes): `d7abf61f51f6db03911fe677adae9f91401ae9eed9dcae90b7ffe35d700a257f`; Git blob `6c2452f92b4729a059b3a0d8291beea31ff0c9c6`.

## 80j: single controlled userland write

The source initializes the marker to `0x41414141`, issues thread creation, and prints the syscall return, protected-call status, marker readback, and thread ID in one line. The [223100 capture](https://github.com/ZigZagBoi1/PS5-14.10-Research/blob/9c89819cf74002b616108bd674b398ae919b40b6/results/phase17_new_vectors/80j_two_stage_20261019_223100.txt), SHA-256 `44b9dbdc2ec581daf122d20d88feb547177ffcd1456717c25d5434f353237b22`, shows the baseline `0x41414141`, the call, then `RV=0x0 OK=true M=0xDEADBEEF` and a nonzero TID. This directly supports the claimed **one userland marker write in that saved capture**.

The capture is mixed with binary output from the harness, and several sibling runs are incomplete or report `M=0`. That is consistent with intermittent or capture-sensitive behavior, but it does not invalidate the complete positive line. The record is not independently authenticated, and the audit did not repeat it. Source SHA-256 (Git commit blob bytes): `c4e2ff6245d64c09aeab79053414f88f8dcb1a954ef5dd8f3189c8cdf592089c`; Git blob `0cc8bf0e202a56b644359d407c2af1ce868029f2`.

## 80k: three-write chain

The [Lua source](https://github.com/ZigZagBoi1/PS5-14.10-Research/blob/9c89819cf74002b616108bd674b398ae919b40b6/probes/phase17_new_vectors/80k_rop_chain.lua) initializes three allocated dwords to distinct sentinels, lays out a three-write chain, calls thread creation, and prints three post-call reads. The [224016 raw capture](https://github.com/ZigZagBoi1/PS5-14.10-Research/blob/9c89819cf74002b616108bd674b398ae919b40b6/results/phase17_new_vectors/80k_rop_chain_20261019_224016.txt), SHA-256 `31d3f149a4c7f4694c5441de4af449f3749bde9d029cb445e9040e882b30a875`, records:

- Initial sentinels `41414141 42424242 43434343`.
- A 14-entry chain and successful-looking `RV=0x0 OK=true` return with nonzero TID.
- Readbacks `m0=DEADBEEF m4=CAFEBABE m8=12345678`.

This is **VERIFIED FROM RAW EVIDENCE** under the limited definition used here: the published source predicts the state transition and a saved capture contains the before/after values plus call result. It supports a reported three-write userland ROP operation. The separate final `DONE` banner is absent from this capture, but the full operation-result line with all three postconditions is present. It does not independently prove capture origin, firmware version, or execution environment. The trailing binary bytes do not obscure the ASCII result line. The earlier [223328 capture](https://github.com/ZigZagBoi1/PS5-14.10-Research/blob/9c89819cf74002b616108bd674b398ae919b40b6/results/phase17_new_vectors/80k_rop_chain_20261019_223328.txt) stops during gadget scanning; a [223354 attempt](https://github.com/ZigZagBoi1/PS5-14.10-Research/blob/9c89819cf74002b616108bd674b398ae919b40b6/results/phase17_new_vectors/80k_rop_chain_20261019_223354.txt) reaches chain setup but has no write readback. These are failed/incomplete attempts, not evidence against the later positive result line.

Source SHA-256 (Git commit blob bytes): `23f98a5341d7aa4b3e3e9c45d7421b35e1903c5b1e31bc4cc6d7d7048799dcc2`; Git blob `2bab3056f985c5273a80924c5eecc307d41cd112`.

## Security boundary

The source and capture document thread-context control and writes into memory allocated by the userland test. No capture reports a kernel address-space operation, kernel read/write, privilege transition, vulnerable kernel component, or hypervisor effect. No vulnerability has been verified on PS5 firmware 14.10 by these results. They must not be described as a kernel exploit or jailbreak.
