# Firmware compatibility evidence

## Available local artifact

The supplied PS5 update package is a 1,261,408,256-byte SLB2 wrapper with SHA-256 `c17384946df6e5c85b2d72cbeee2057b165bf90279d9e2a86d527d0778cdaaf6`. The local parser validates wrapper metadata and locates the `PS5UPDATE1.PUP` payload entry. The inner payload remains opaque in this workflow: no decryption, extraction, Sony key use, or proprietary binary inspection was performed. The wrapper hash does not prove the contents of WebKit, JavaScriptCore, FreeBSD-derived kernel code, or hypervisor.

## Candidate mapping

| Candidate | Public upstream range/patch evidence | What would prove 14.10 compatibility | Current classification |
|---|---|---|---|
| CSSFontFace UAF, CVE-2026-43715 | WebKit fix `5aedb82710ba578f`; Apple advisory | Authorized 14.10 WebKit build/source revision compared with the fix, or reliable binary diff | **POSSIBLE — INSUFFICIENT EVIDENCE** |
| TransformStream, CVE-2026-43705 | WebKitGTK / Apple advisory | Same mapping plus reproduction evidence tied to PS5 build | **CONFIRMED UPSTREAM ONLY** |
| UnlinkedMetadataTable, CVE-2026-64784 | WebKitGTK advisory; no Sony source | Exact size arithmetic and patched implementation in the target build | **POSSIBLE — INSUFFICIENT EVIDENCE** |
| FreeBSD CVE-2026-7270 and CVE-2026-45251 | FreeBSD advisories | Sony fork provenance, matching function, patch state, syscall reachability | **CONFIRMED UPSTREAM ONLY** |
| Gezine's reported 14.10 kernel method | Debug Settings demonstration and statements reported publicly | Reproducible public method, target-specific artifact, independent kernel R/W verification | Mechanism **NOT TESTED / UNDISCLOSED** |

The separate public 14.10 research repository reports native userland ROP and controlled user-memory writes but explicitly reports no demonstrated kernel R/W and no validated target kernel vulnerability. This observation concerns that project's probes; it does not identify Gezine's method.

## Browser-build and hypervisor limits

The saved browser logs include a reported PS5/14.10 user agent, which is not cryptographic firmware attestation. No browser build ID or Sony source revision in the local evidence binds upstream WebKit commits to the console. Public reporting says the 13.xx kernel method Gezine used was patched at 14.00; separate scene reporting says an HV flaw was patched at 14.10, but this audit found no Sony patch diff to independently verify those patch boundaries. Keep the HV patch statement as attributed reporting, not source-confirmed compatibility.

## Safe next evidence

Record official package provenance and device-reported version separately; seek lawful, authorized source/build identification; compare only public or authorized artifacts; preserve hashes, tool versions and exact line-level diffs. Do not infer code presence from version strings, entropy, file size, a missing beacon, or a crash.
