# PS5 14.10 WebKit security and boundary review

**Audit date: 20 October 2026. Base commit: `71b0968`.** Public-source analysis and two fresh, bounded live tasks were completed. No new exploitable vulnerability, native memory primitive, kernel access or filesystem-directory access was demonstrated.

## Findings in plain English

1. **The best verifiable source baseline is Sony's mixed `WebKit_1400` publication, not “Safari 17.0.”** Some sampled files match a 2023 upstream snapshot; others contain later fixes. There is no demonstrated whole-tree upstream revision or exact 14.10 executable correspondence.
2. **New source finding:** Sony's `ProxyObject.cpp` exactly matches the file at a March 2024 receiver-sanitization fix. Its structured-clone source also contains object-pool separation, separate keep-alive storage and tag validation associated with the January 2024 fix. This contradicts a blanket assumption that an old version file means those components retain the original unchecked implementations.
3. **CSSFontFace and metadata arithmetic remain source leads, not verified 14.10 vulnerabilities.** The previously acquired Sony files still hash to the recorded old implementations. TransformStream already contains the relevant result-count/type safeguards.
4. **Relapse's public project supports 7.00–13.60.** Its README does not offer 14.10 support. The public CSSFontFace project likewise distinguishes claimed bug scope, exploitability and the chain it supplies; none establishes a usable 14.10 chain.
5. **The live browser enforces the sampled iframe/CSP controls.** FontFace and TransformStream are exposed. These are capability and policy observations, not proof of engine memory safety or exploitability.

## Evidence quality and scope

| Evidence level | Used here | What it cannot establish |
| --- | --- | --- |
| Manufacturer source release | Current Sony listing and authorized source members with SHA-256/ZIP CRC checks | Exact production binary, private backports, compiled configuration or reachability |
| Upstream patch/advisory | Immutable WebKit commits and official GTK/WPE advisories | Sony firmware affected ranges without target mapping |
| Researcher's own publication | Pinned author READMEs and published patch descriptions | Independently authenticated console outcome or unsupported firmware compatibility |
| Developer Wiki | Community index, ranges and links to primary patches | Independent verification of each version/patch claim |
| Live bridge record | New authenticated session results with timestamps, source hashes and raw-event references | Hardware attestation, native memory access, full sandbox integrity or kernel state |

The [evidence JSON](PS5_1410_WEBKIT_SECURITY_EVIDENCE_20261020.json) records source URLs, pinned revisions, measured hashes, access failures and live evidence. API credentials are excluded. Prior reports/logs remain preserved; the previous live-log prefix was hash-checked after this phase appended new events.

## 1. Sony source baseline and provenance

Sony's [PS5 WebKit listing](https://www.playstation.com/en-us/oss/ps5/webkit/) currently associates the [official `WebKit_1400.zip`](https://www.playstation.com/content/dam/global_pdc/en-us/external-resources/oss/PS5/webkit/WebKit_1400.zip) with **14.00 onward**. The preceding range ends at 14.00, so the listing is not a precise component manifest. The [separate JavaScriptCore listing](https://www.playstation.com/en-us/oss/ps5/webkit-javascriptcore/) still offers `JSC-800.zip` under an open 8.00-onward range. That standalone package was not reacquired; JSC source embedded in the newer WebKit publication was examined directly instead.

The existing source inventory was rehashed. Two additional Sony members were acquired through validated HTTP ranges and ZIP CRC checks: `SerializedScriptValue.cpp` and `ProxyObject.cpp`. This acquisition transferred **73,457,089 bytes**, mainly directory metadata, from a **1,637,794,253-byte** archive. A whole-archive SHA-256 was **not** measured. Members stayed in ignored `derived/`; only hashes and analysis are committed.

| Source observation | Exact reference | Meaning |
| --- | --- | --- |
| Source version is `616.1.27.211.1` | `Configurations/Version.xcconfig:24–28`; prior member provenance rechecked | A publication's version value, not a complete production revision |
| UA uses fixed engine/browser tokens | `UserAgentPlayStation.cpp:64,71`: `605.1.15` and `Version/17.0` | A matching live UA cannot identify the exact WebKit commit |
| JIT/FTL/DFG defaults are OFF | `OptionsPlayStation.cmake:206–208` | Relevant build defaults; production overrides remain unknown |
| CSSFontFace pair matches older upstream files | Exact file hashes at [`0e722583a4d695c7b25f384c61fbf5b59b4c3146`](https://github.com/WebKit/WebKit/tree/0e722583a4d695c7b25f384c61fbf5b59b4c3146), committed 2023-09-15 | A per-file baseline, not a whole-engine identity |
| Proxy implementation matches a later fixed file | Exact `ProxyObject.cpp` match at [`ceb7e89febcd92b46d65396ce68e0d58ae6bcd6e`](https://github.com/WebKit/WebKit/commit/ceb7e89febcd92b46d65396ce68e0d58ae6bcd6e), committed 2024-03-14 | Direct counterexample to whole-build age inference |

**New member fingerprints:**

- `Source/JavaScriptCore/runtime/ProxyObject.cpp`, 54,092 bytes: `aaa5adf496305e09d3f6eb1c249b3ce576aa6165fe6434855b34d85abaaedbf7`.
- `Source/WebCore/bindings/js/SerializedScriptValue.cpp`, 202,646 bytes: `4e8d3814d9ed0fb1b233ddcb70c01029d32c503c1b2c2b430f0f81a58bf7d3ca`.

### New comparison: proxy receiver sanitization

The upstream [March 2024 patch](https://github.com/WebKit/WebKit/commit/ceb7e89febcd92b46d65396ce68e0d58ae6bcd6e) addresses internal scope values reaching Proxy handlers. Sony's entire inspected `ProxyObject.cpp` is byte-identical to that fixed file and differs from its parent. Its get/set paths sanitize receivers at Sony lines **190** and **520**.

This is a verified **file-level fix observation**. The upstream change touches seven other files, including inline helpers and bytecode-generation code. Those were not all compared, and later related fixes exist. Consequently this result does not establish that the complete leak family is closed in the published tree or the 14.10 executable.

### New comparison: structured-clone object pools

The [January 2024 upstream patch](https://github.com/WebKit/WebKit/commit/010c6bdfb0cde0485d31f0260ab9a046fa9b8567) separates graph-reference indexing from objects retained only for lifetime protection. Sony's inspected file has the corresponding central safeguards:

- **Line 900:** a dedicated `m_objectPool`.
- **Lines 1142–1188:** tag-constrained reference/pool insertion helpers.
- **Line 2487:** separate `m_keepAliveBuffer`.
- **Lines 2646/2668:** temporary iterator/value retention uses the keep-alive buffer.
- **Line 4368:** deserialization records the boxed BigInt in the object pool.

The file is not byte-identical to either that upstream revision or the older reference. These observations establish specific safeguards, not complete patch equivalence or the absence of every clone/GC bug. Neither an exploit regression nor exceptional serialization objects were executed.

## 2. Candidate vulnerability comparison

Ranking reflects the value of further **safe evidence collection**, not an exploit success probability.

| Candidate | Prerequisites / published limitations | Patch/source evidence | 14.10 conclusion / confidence |
| --- | --- | --- | --- |
| **CSSFontFace backing lifetime**, upstream CVE-2026-43715 / Bug 313577 | Relevant native lifetime/reentrancy path; API presence alone is insufficient | Sony's recorded `FontFace.cpp:358` lacks the backing pin; `CSSFontFace.cpp:55` lacks the later membership guard. [Lifetime fix](https://github.com/WebKit/WebKit/commit/f3d61dae1b61dfbd2fc0b01196b63f8769bca77e) and [follow-up](https://github.com/WebKit/WebKit/commit/f1fff08a99d77bac49c2500ece3fdcfac06c8f1c) inspected. | **Plausible source lead; target unknown.** High source confidence; no target memory fault. |
| **UnlinkedMetadataTable arithmetic**, CVE-2026-64784 / Bug 317632 | Reachable generated metadata exceeding checked representation/allocation bounds; build limits and actual allocation outcome matter | Sony's old unsigned offset/count arithmetic is preserved. [Fix `97df94e…`](https://github.com/WebKit/WebKit/commit/97df94ead028cddcfc21e48ec6f2f72d25ec1662) adds checked calculations and failure propagation. Offline source diff regenerated. | **Plausible source lead; target unknown.** Arithmetic/source evidence is not heap-corruption evidence. Corrected V480 remains negative for its specific prior claim. |
| **TransformStream type confusion**, CVE-2026-43705 / Bug 314528 | Altered stream-initialization result path; ordinary API exposure does not exercise it | Sony's prior inspected file already has result-count and type checks corresponding to [fix `8fd92b1…`](https://github.com/WebKit/WebKit/commit/8fd92b1021d310b2580eb3ac7913911eb14dc476). | **The specific unchecked-result hypothesis is contradicted in published source.** Exact executable state unknown. No trigger run. |
| **Clone object-pool mismatch**, no CVE assigned here | Serializer/deserializer graph invariants; a complete chain also needs other capabilities | New Sony source contains separated pools, tag checks and relevant object-pool handling; compared with [`010c6bd…`](https://github.com/WebKit/WebKit/commit/010c6bdfb0cde0485d31f0260ab9a046fa9b8567). | **Blanket unpatched-source claim unsupported.** Relevant safeguards observed; complete family/executable status unknown. |
| **Proxy/internal-scope leak family**, no CVE assigned here | Internal receiver must reach JS without sanitization; different execution paths require separate checks | Exact fixed `ProxyObject.cpp` match at [`ceb7e89…`](https://github.com/WebKit/WebKit/commit/ceb7e89febcd92b46d65396ce68e0d58ae6bcd6e). Other helpers/later changes not fully inspected. | **Fixed inspected file; incomplete family mapping.** No scope-leak probe or address disclosure attempted. |
| **Public CSSFontFace exploit project** | Author claims bug scope through PS5 13.40, narrower exploitability through 8.60, and layout/ASLR/vtable limitations. The supplied chain lists PS5 support as N/A. | [Pinned author README](https://github.com/ntfargo/CSSFontFace-Exploit/blob/221baa6e7349b96a6fd299808a25a4178e47741c/README.md). No public-project 14.10 support established. | **Author claims and engineering limits, not 14.10 verification.** Do not automatically assign every similarly named font issue the same CVE. |
| **Relapse complete chain** | Browser primitives followed by a separate native/kernel stage | [Pinned author README](https://github.com/ntfargo/Relapse-Exploit/blob/dd8e4e0914c5e9d066ee1f9b056be76cb992c8e0/README.md) states 7.00–13.60 and describes distinct browser/kernel stages. | **14.10 unsupported by the reviewed public project.** This does not prove every constituent bug is patched. No kernel code audited/executed here. |

The official [GTK/WPE July advisory](https://webkitgtk.org/security/WSA-2026-0004.html) confirms the first and third CVE identifiers and gives affected ranges for those ports before 2.52.5. The [September advisory](https://webkitgtk.org/security/WSA-2026-0006.html) associates the metadata issue with versions before 2.54.0. These are **GTK/WPE product ranges, not Sony firmware ranges**. The membership follow-up's maintainer describes the lifetime backport as security-complete and the remaining failure as a stress-mode assertion; a missing membership check alone is not equivalent to an unpatched lifetime UAF.

## 3. Public claims and evidence gaps

The [PS5 Developer Wiki vulnerability page](https://www.psdevwiki.com/ps5/Vulnerabilities) is a useful index of browser, kernel and hypervisor boundaries. Its linked [WebKit bugs page](https://www.psdevwiki.com/ps4/WebKit_Bugs) reports version-dependent fixes and contains explicit uncertainty. It also mixes “tested” and “untested” notes across related entries. These are community reports requiring primary-source corroboration. Its reported 14.00 Proxy/stream changes are consistent with safeguards observed in Sony's source, but that is not independent validation of the wiki's complete firmware matrix. Direct HTTP fetches returned errors; the web research reader could view both pages. No immutable wiki revision was captured.

The author's [CSSFontFace article URL](https://linearfox.com/blog/cssfontface-uaf-playstation) returned a JavaScript loading shell to the research reader. Full article content was not independently assessed in this phase; claims above rely on the pinned README and inspected primary patches instead. No cited exploit host or payload was opened on the PS5.

Reports of Gezine's 14.10 Debug Settings result remain separate from these candidates. The earlier [original-post review](GEZINE_1410_RESEARCH.md) records an [X post](https://x.com/gezine_dev/status/2112279793911968218) and its media-access limitation. This phase did not independently authenticate that video or obtain a disclosed 14.10 method. Nothing examined links that result to CSSFontFace, metadata arithmetic or Relapse. No source for a reproducible 14.10 chain was established in the reviewed projects; this is not an exhaustive claim about all private/public research.

Remaining technical gaps include production component identity, complete vendor patch coverage, exact build options, path reachability and actual memory-safety evidence. One requested archive member, `parser/NodesCodegen.cpp`, was absent at that requested path; the upstream fix identifies `bytecompiler/NodesCodegen.cpp`. That correct path was not acquired here. The failed lookup is not evidence that Sony lacks the component.

## 4. Fresh live validation

The authenticated bridge confirmed **`a93285a84852` ONLINE at 22:21:14 UTC / 23:21:14 BST**, with a heartbeat at **22:21:08 UTC**. The existing service and task catalog were reused without a restart or new client pairing. Only two fixed categories were scheduled:

| Task | Job ID | Completion UTC | Raw evidence |
| --- | --- | --- | --- |
| surface | `a41ad918204f7c72` | 22:21:40.550796 | Existing `events.ndjson`, line 6 |
| security | `dd07ae9bba05914e` | 22:21:42.769009 | Existing `events.ndjson`, line 8 |

Both completed with all **29 expected observations**. No desktop browser run is presented as target evidence. Context: reported PS5/14.10, AppleWebKit/605.1.15 and Version/17.0; origin `http://192.168.4.29:8765`; secure context and cross-origin isolation false. All new error fields were `""`; there was no recorded crash or exception.

| Observed target result | Evidence | Interpretation |
| --- | --- | --- |
| FontFace, font set and TransformStream exposed | `surface.FontFace`, `surface.fontSet`, `surface.TransformStream`, line 6 | Capability only. No font load, reentrant font sequence or stream vulnerability trigger was performed. |
| Controlled sandbox frame had opaque origin and blocked parent DOM access | `security.sandbox`, line 8 | Sampled HTML sandbox behavior worked; this does not validate the OS process sandbox. |
| Static CSP control loaded while forbidden inline script did not execute | `security.csp`, line 8 | Expected policy behavior in this controlled frame; not comprehensive CSP coverage. |
| Small Blob-backed worker returned its expected marker | `security.worker`, line 8 | Ordinary worker execution, not native execution or privileged access. |
| WebAssembly and Permissions API not exposed | `security.wasm`, `security.permissions`, line 8 | Current-context absence. No permanent-disablement conclusion or missing-API exception invented. |
| Service Worker and subtle WebCrypto absent on insecure HTTP | `security.serviceWorker`, `security.crypto`, line 8 | Secure-context retest needed; support over HTTPS remains unknown. |

No poisoned iterators, prototype hooks, scope-leak programs, GC/heap pressure, large generated programs, arbitrary memory operations or kernel payloads were run. API presence and successful policy checks cannot serve as a patch oracle for the candidate bugs.

## 5. Current security and filesystem boundaries

| Boundary | Established status |
| --- | --- |
| Ordinary webpage JavaScript / browser-managed data | Working within recorded tests. Prior [file-interface evidence](PS5_FILE_INTERFACES_20261020.md) confirms exact 47-byte in-memory FileReader and Blob readback. |
| User-selected files | Still **NOT ESTABLISHED**: manual picker observations were uncertain and no selected synthetic file read was validated. |
| Native filesystem interfaces / actual PS5 directories | Still **NOT ESTABLISHED**. Prior HTTP type checks returned undefined for the tested pickers/filesystem interfaces; no actual OS path or directory listing was acquired. |
| WebKit memory-corruption primitive / native browser execution | **NOT ESTABLISHED** by these page diagnostics. Browser JS and worker execution do not establish arbitrary native memory access. |
| Browser process sandbox escape, kernel R/W, debug access, hypervisor compromise | **NOT ESTABLISHED** in this investigation. HTML iframe restrictions are a different boundary from native process isolation. |

The prior TXT/Blob download and instrumented-navigation outcomes remain inconclusive. This phase did not repeat those manual tests, perform directory enumeration, read personal files or write console storage.

## 6. Three highest-value safe experiments

1. **Complete the offline vendor patch-family comparison.** Acquire the correct bytecompiler and ProxyHelpers members through the same bounded, CRC-checked source workflow; compare all files from the relevant upstream fixes, including later related commits. Success means exact source evidence and a clear residual gap list—not a production-vulnerability verdict. Seek an authorized signed component/build mapping before promoting any source finding to firmware applicability.
2. **Controlled HTTP/HTTPS context comparison.** If an already trusted, IP-valid certificate is available, run the identical bounded API/policy suite on the same console in both contexts, preserving origins, hashes and errors. No certificate bypass, trust installation or permission evasion. This can separate context prerequisites from some missing API observations; it cannot establish a security patch level.
3. **Tiny ordinary serialization/stream conformance controls.** Add a reviewed fixed task for a few plain, acyclic values and small typed arrays (at most 1 KiB, no custom getters/prototype changes, transfers, GC pressure or stress loops). Check exact roundtrip content and one ordinary stream completion against documented expected behavior. Success provides a normal-path baseline; an error remains a standards/debugging observation until its cause is independently established. Do not substitute public exploit regressions for these controls.

## Reproduction and preservation

The existing offline tool was rerun on the pinned Sony CSSFontFace manifest and on the metadata before/fixed source pair. Results remain in fresh ignored paths under `derived/security-boundaries-20261020/`. No engine was built or installed. Reproduce using new output names:

```powershell
Set-Location E:\PS5-FW-14.10-Research
python -S tools/ps5_research.py --webkit-snapshot derived\webkit-deep\sony-1400\snapshot.json --format json --output derived\sony-source-review-new.json
python -S tools/ps5_research.py --compare derived\phase4\sony-additional\Source\JavaScriptCore\bytecode\UnlinkedMetadataTable.cpp derived\phase4\metadata-97df94ead028cddcfc21e48ec6f2f72d25ec1662.cpp --output derived\metadata-review-new.json
```

Those commands require the authorized local source snapshots already present here. The committed evidence contains hashes and references, not Sony binaries, keys, exploit payloads or fabricated successes. Changes are committed locally only; no GitHub push was authorized for this phase.
