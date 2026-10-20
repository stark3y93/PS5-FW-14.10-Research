# Firmware compatibility evidence

## Available local artifact

The supplied PS5 update package is a 1,261,408,256-byte SLB2 wrapper with SHA-256 `c17384946df6e5c85b2d72cbeee2057b165bf90279d9e2a86d527d0778cdaaf6`. The local parser validates wrapper metadata and locates the `PS5UPDATE1.PUP` payload entry. The inner payload remains opaque in this workflow: no decryption, extraction, Sony key use, or proprietary binary inspection was performed. The wrapper hash does not prove the contents of WebKit, JavaScriptCore, FreeBSD-derived kernel code, or hypervisor.

## Candidate mapping

| Candidate | Public upstream range/patch evidence | What would prove 14.10 compatibility | Current classification |
|---|---|---|---|
| CSSFontFace UAF, CVE-2026-43715 | Sony WebKit_1400 published files match older upstream source and lack the two safeguards; main/stable fix history independently compared | Exact 14.10 browser executable/source correspondence, including backports and production changes | **Published source old; exact firmware UNKNOWN** |
| TransformStream, CVE-2026-43705 | WebKitGTK / Apple advisory | Same mapping plus reproduction evidence tied to PS5 build | **CONFIRMED UPSTREAM ONLY** |
| UnlinkedMetadataTable, CVE-2026-64784 | WebKitGTK advisory; published Sony source not matched to the exact target allocation function | Exact size arithmetic and patched implementation in the target build | **POSSIBLE — INSUFFICIENT EVIDENCE** |
| FreeBSD CVE-2026-7270 and CVE-2026-45251 | FreeBSD advisories | Sony fork provenance, matching function, patch state, syscall reachability | **CONFIRMED UPSTREAM ONLY** |
| Gezine's reported 14.10 kernel method | Debug Settings demonstration and statements reported publicly | Reproducible public method, target-specific artifact, independent kernel R/W verification | Mechanism **NOT TESTED / UNDISCLOSED** |

The external userland evidence is reviewed in [PROBE_80I_80K_VERIFICATION.md](PROBE_80I_80K_VERIFICATION.md). Later 80j/80k captures contain source-matched userland marker readbacks; the old 80k scan-only capture is not the only result. Those self-published records do not establish a firmware vulnerability or identify Gezine's method.

## Browser-build and hypervisor limits

The saved browser logs include a reported PS5/14.10 user agent, which is not cryptographic firmware attestation. Sony-published WebKit_1400 now supplies manufacturer source evidence and selected upstream file matches, but no exact 14.10 browser build ID or executable correspondence binds those files to the console. Public reporting says the 13.xx kernel method Gezine used was patched at 14.00; separate scene reporting says an HV flaw was patched at 14.10, but this audit found no Sony patch diff to independently verify those patch boundaries. Keep the HV patch statement as attributed reporting, not source-confirmed compatibility.

## Safe next evidence

Record official package provenance and device-reported version separately; seek lawful, authorized source/build identification; compare only public or authorized artifacts; preserve hashes, tool versions and exact line-level diffs. Do not infer code presence from version strings, entropy, file size, a missing beacon, or a crash.

## Updated source evidence

The published source version is `616.1.27.211.1`; the browser user-agent tokens `605.1.15` and `17.0` are hardcoded in the Sony port. Two font source files and the version file match pinned upstream files, while sampled platform options and user-agent code differ. This establishes selected-file lineage and vendor changes, not a whole-tree revision. See [PS5_1410_WEBKIT_PROVENANCE.md](PS5_1410_WEBKIT_PROVENANCE.md) and [WEBKIT_EVIDENCE_GAPS.md](WEBKIT_EVIDENCE_GAPS.md).
