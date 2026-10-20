# PS5 14.10: complete published patch comparisons and production uncertainty

Base: `e59d638`. Research date: 20 October 2026. This continues the [previous source review](PS5_1410_WEBKIT_SECURITY_REVIEW_20261020.md). No console tests were repeated, no exploit regression was executed, and no firmware binary was read or modified.

## Conclusions and classification rules

**CONFIRMED IN SOURCE** means a directly observed property of the licensed Sony publication, including a verified absence of a specific safeguard. It does not mean a vulnerability is confirmed in the console. **CONFIRMED IN PRODUCTION** requires target-specific evidence of the stated property. **NOT VERIFIED** means the required evidence was not obtained. **INCONCLUSIVE** means available evidence does not settle the broader claim.

| Question | Published source conclusion | Production firmware 14.10 conclusion |
| --- | --- | --- |
| CSSFontFace lifetime pin and copied-client membership guard | **CONFIRMED IN SOURCE:** both inspected paths retain their older forms; the identified safeguards are absent | **NOT VERIFIED:** exact executable correspondence, triggering lifetime path and memory fault |
| Metadata checked arithmetic and error propagation | **CONFIRMED IN SOURCE:** the identified fix is absent across all five implementation/header/caller files | **NOT VERIFIED:** runtime bounds, reachability, production backports and memory corruption |
| March 2024 Proxy receiver fix | **CONFIRMED IN SOURCE:** the coordinated seven-file implementation is represented, including helpers, intrinsic registration, bytecompiler and DFG handling | **NOT VERIFIED:** exact production implementation; this does not close every scope-related bug |
| January 2024 structured-clone pool fix | **CONFIRMED IN SOURCE:** core pool separation, tagged accounting, primitive BigInt handling and optional debug validation are represented across both changed source files | **NOT VERIFIED:** full production patch state; **INCONCLUSIVE** for equivalence of every vendor-specific serialization case |
| Related DFG array-iterator ToThis fix | **CONFIRMED IN SOURCE:** the two inspected paths retain the pre-fix behavior | **NOT VERIFIED:** DFG production enablement and target exposure; source defaults disable DFG/JIT |
| Later wholesale scope refactor | **CONFIRMED IN SOURCE:** inspected Sony code retains the older architecture. Upstream merge was reverted and the subsequent reland PR remains open | **INCONCLUSIVE:** absence of a reverted/open refactor does not establish a missing required security fix |
| Exact source-to-production build mapping | **NOT VERIFIED:** the reviewed Sony material has a broad firmware label and component version, without an exact executable mapping | **NOT VERIFIED:** no matching production build manifest or authorized executable comparison |

No candidate vulnerability or candidate security fix is **CONFIRMED IN PRODUCTION** by this phase. Prior real PS5 capability observations remain separate evidence and are not upgraded into patch detection.

## Evidence and method

The [machine-readable comparison evidence](PS5_1410_WEBKIT_PATCH_FAMILY_EVIDENCE_20261020.json) contains full upstream commit/parent identifiers, per-file SHA-256 values, Sony ZIP-member CRC values, exact-match results, source excerpts with line numbers, PR states and scope limitations. It includes every `Source/` path changed by the five primary fix commits, and expanded comparisons for related scope changes and the reverted refactor. Regression-test filenames are inventoried from commit metadata only; tests were not executed.

Coverage: **16 primary-fix source-file comparisons**, **186 fixed/parent/vendor comparison records** across **14 resolved commits**, **89 Sony member records** (including two exact-path gaps), and **57 checked source markers**. Comparison records include overlapping files at different revisions; they are not independent vulnerability counts or runtime tests.

Sony members were read from its [official WebKit_1400 archive](https://www.playstation.com/content/dam/global_pdc/en-us/external-resources/oss/PS5/webkit/WebKit_1400.zip) using validated HTTP 206 ranges and ZIP CRC checks. No whole-archive hash was measured. Local source, upstream parents/fixed files and generated diffs are retained under ignored `derived/patch-family-20261020/`. Original logs and earlier source snapshots remain preserved.

All implementation/header paths of the five primary fixes were available in Sony's archive. For the much larger reverted scope refactor, two upstream paths were absent at their exact Sony archive paths: `Source/JavaScriptCore/runtime/JSIteratorPrototype.cpp` and `Source/WebCore/bindings/js/JSDOMWindowCustom.cpp`. This is an exact-path coverage limitation, not proof of missing functionality. Historical `ChangeLog` content was not treated as implementation. No engine was built and no compiler/runtime regression test was run.

Exact byte matches are strong file evidence. Changed-line membership is only an aid to manual review: repeated boilerplate, renamed types, older APIs and configuration guards prevent it from establishing semantic patch equivalence on its own. Full fixed-to-Sony diffs and affected control-flow context were inspected for the primary fixes. The larger reverted refactor was inventoried across available changed source paths, with architecture markers reviewed; it is not claimed to be semantically equivalent to either upstream snapshot.

## 1. CSSFontFace: lifetime protection and related client handling

Primary references:

- [Lifetime backport `f3d61dae1b61dfbd2fc0b01196b63f8769bca77e`](https://github.com/WebKit/WebKit/commit/f3d61dae1b61dfbd2fc0b01196b63f8769bca77e), Bug 313577, `FontFace::loadForBindings`.
- [Client-membership follow-up `f1fff08a99d77bac49c2500ece3fdcfac06c8f1c`](https://github.com/WebKit/WebKit/commit/f1fff08a99d77bac49c2500ece3fdcfac06c8f1c), Bug 318530, CSSFontFace client iteration.
- [Mainline membership change `5aedb82710ba578f61501106e78f6b25b7f7a558`](https://github.com/WebKit/WebKit/commit/5aedb82710ba578f61501106e78f6b25b7f7a558), resolved through [PR 68176](https://github.com/WebKit/WebKit/pull/68176).

**CONFIRMED IN SOURCE:** Sony `Source/WebCore/css/FontFace.cpp:358–362` calls `m_backing->load()` directly. The backport instead uses `protect(m_backing)->load()` to retain the backing during a call that may re-enter and alter ownership. Sony `CSSFontFace.cpp:55–58` invokes the copied clients without the follow-up's `clients.contains(client)` guard. The older Sony client type/signature differs from the newer branch, but the callback/lifetime distinction remains visible.

The follow-up's own explanation explicitly says the backing-pin security fix was complete before the membership follow-up; the remaining observed failure was a stress-mode debug assertion in `CSSFontFaceSet::fontStateChanged`. Therefore a missing membership guard alone is not evidence of the lifetime UAF. Here the lifetime path itself was also inspected and lacks that identified pin.

The original branch hash `d90247302507`, named in the backport, returned GitHub API HTTP 422. Its exact original tree was not obtained. The public backport and separately resolved mainline follow-up were inspected instead. Do not describe the follow-up as a new, independently confirmed PS5 UAF.

**NOT VERIFIED:** production source correspondence, native lifetime failure and exploitability on 14.10. `FontFace` API exposure does not answer any of these questions. No fonts or reentrant callbacks were used this phase.

## 2. Metadata arithmetic: complete failure path

[Fix `97df94ead028cddcfc21e48ec6f2f72d25ec1662`](https://github.com/WebKit/WebKit/commit/97df94ead028cddcfc21e48ec6f2f72d25ec1662), Bug 317632, adds both bounds checking and caller error handling. Its original branch reference resolves to [`9343a9521f58b200abfd3b3fa854989342349d47`](https://github.com/WebKit/WebKit/commit/9343a9521f58b200abfd3b3fa854989342349d47); both revisions and parents were compared.

| Coordinated source path | Upstream fix | Sony source observation / status |
| --- | --- | --- |
| `bytecode/UnlinkedMetadataTable.cpp`, `UnlinkedMetadataTable::finalize` | Checked offset multiplication/addition, alignment-overflow rejection, value-profile/biased-allocation bounds, cleanup and false return | **CONFIRMED IN SOURCE:** old unsigned arithmetic at lines 110–147, including multiplication/addition at 129; no corresponding checked failure branch |
| `bytecode/UnlinkedMetadataTable.h` | `[[nodiscard]] bool finalize()` | **CONFIRMED IN SOURCE:** `void finalize()` at 77 |
| `bytecode/UnlinkedCodeBlockGenerator.cpp`, `finalize` | Capture metadata failure and return it after normal finalization bookkeeping | **CONFIRMED IN SOURCE:** void implementation at 116, unchecked call at 123 |
| `bytecode/UnlinkedCodeBlockGenerator.h` | Boolean finalization declaration | **CONFIRMED IN SOURCE:** void declaration at 197 |
| `bytecompiler/BytecodeGenerator.cpp`, `generate` | Convert failed finalization into parser OutOfMemory | **CONFIRMED IN SOURCE:** unconditional finalization at 332; later `m_expressionTooDeep` OOM check is a different condition |

This is stronger than finding one unchecked expression: the entire named fix's detection-and-propagation chain is absent in the inspected tree. It is still not a demonstrated corrupting allocation. Existing compiler limits, actual metadata sizes, memory limits and production changes can alter exposure. The prior corrected V480 negative result remains valid for its specific earlier claim.

**CONFIRMED IN SOURCE:** Sony also uses an older metadata layout: this `finalize` implementation reallocates offset-table storage and its header's `totalSize()` returns the final offset directly. It does not contain the newer fix parent's `m_numValueProfiles`/`valueProfileSize` allocation arrangement. The newer patch's individual value-profile and allocation changes therefore cannot be transplanted into an assertion that the older Sony code has exactly the same allocation failure. What is directly established is the unchecked offset arithmetic and absent failure-propagation contract. Actual allocation/linking consequences require a separate review of the older design.

**NOT VERIFIED:** production reachability or corruption. No large source generation, large allocations, overflowing metadata compilation or original stress test was attempted.

## 3. Proxy and internal-scope changes: distinguish separate fixes

### Coordinated March 2024 fix

[`ceb7e89febcd92b46d65396ce68e0d58ae6bcd6e`](https://github.com/WebKit/WebKit/commit/ceb7e89febcd92b46d65396ce68e0d58ae6bcd6e), Bug 267425, sanitizes receiver values before Proxy traps. Original branch [`e3a75800fe85ad1e9907a55ec5bbf9e7742607b9`](https://github.com/WebKit/WebKit/commit/e3a75800fe85ad1e9907a55ec5bbf9e7742607b9) was also resolved and compared.

**CONFIRMED IN SOURCE:** all seven changed source files were acquired and examined:

| Path under `Source/JavaScriptCore/` | Affected functions/role | Sony comparison |
| --- | --- | --- |
| `runtime/ProxyObject.cpp` | `performProxyGet`, `ProxyObject::performPut` | Entire file exactly matches fixed March source; receiver `toThis(strict)` at 190/520 |
| `builtins/ProxyHelpers.js` | Four get/getByVal/set helpers | Entire file exactly matches fixed March source; all four receiver conversions present |
| `bytecode/BytecodeIntrinsicRegistry.h` | Intrinsic registration | `macro(toThis)` present at 101 |
| `bytecompiler/BytecodeGenerator.h` | General-register overload plus this-register wrapper | Both declarations/entry points present |
| `bytecompiler/BytecodeGenerator.cpp` | `emitToThis(RegisterID* srcDst)` | Uses supplied register and returns it at 5510–5513; older opcode signature lacks the newer profiling argument, so not byte-identical |
| `bytecompiler/NodesCodegen.cpp` | `emit_intrinsic_toThis` | Argument conversion and returned register are present at the correct bytecompiler path |
| `dfg/DFGByteCodeParser.cpp` | `parseBlock`, `op_to_this` | Reads/writes `bytecode.m_srcDst`, rather than assuming the function's this-register |

This closes the previous report's seven-file coverage gap for this specific fix. It does not establish every scope-handling fix or production state.

### Related landed sanitization fixes

| Upstream reference | Full implementation coverage | Sony observation |
| --- | --- | --- |
| [`8a775ddff7e83a62ed4f9999478a4ea2429b4516`](https://github.com/WebKit/WebKit/commit/8a775ddff7e83a62ed4f9999478a4ea2429b4516), canonical 229319 | Array iterator creation, Date primitive/JSON conversion, Error and RegExp string conversion; all four implementation files | **CONFIRMED IN SOURCE:** relevant strict ToThis conversions present, including ArrayPrototype:792, DatePrototype:361/902, ErrorPrototype:76, RegExpPrototype:199 |
| [`711c7de281d5975ec9428ebe0e27f859ee57f022`](https://github.com/WebKit/WebKit/commit/711c7de281d5975ec9428ebe0e27f859ee57f022), canonical 259016 / Bug 250748 | Both Object-toString JIT operations in `DFGOperations.cpp` | **CONFIRMED IN SOURCE:** strict conversion in both untyped/object paths at 416/426 |
| [`ecb7da686a5066eea209b6f4b2b6dcddbd0d551f`](https://github.com/WebKit/WebKit/commit/ecb7da686a5066eea209b6f4b2b6dcddbd0d551f), canonical 272163 / Bug 263408 | Array-iterator intrinsic handling in `DFGByteCodeParser.cpp` and `DFGClobbersExitState.cpp` | **CONFIRMED IN SOURCE:** missing identified ToThis step at parser:2540–2544; exit-state helper:113–118 retains old SideState-only rule |

The last row is a new, narrowly scoped source gap. It depends on optimizing-compiler paths. Sony `OptionsPlayStation.cmake:206–208` defaults JIT, FTL and DFG off. **NOT VERIFIED:** production overrides or execution of the affected DFG path. This is lower priority than establishing build identity/configuration, and is not a PS5 exploit finding.

### A merged refactor, its revert, and an open reland

The community wiki's “fix #2/#3” links lead to broader scope-architecture work rather than two simply cumulative landed security patches:

- [PR 31572](https://github.com/WebKit/WebKit/pull/31572) merged as [`ee167b8fe4fd234a33b2381640cba982fa6c7516`](https://github.com/WebKit/WebKit/commit/ee167b8fe4fd234a33b2381640cba982fa6c7516) on 9 October 2024. It replaces internal-scope-as-this handling with explicit scope checks, changes call generation/opcodes, global wrapping and native call sites.
- [`9bfbbb1fe8f030b8d313a2a97d431b1c50d95d37`](https://github.com/WebKit/WebKit/commit/9bfbbb1fe8f030b8d313a2a97d431b1c50d95d37) reverts that change and its immediate regression follow-up for a reported performance regression.
- [PR 35527](https://github.com/WebKit/WebKit/pull/35527), head `a5667ef806d1608d25effcebf92175fa098cece8`, is open and unmerged in the freshly retrieved GitHub metadata. The PR is mutable.

Both landed/refactor and revert commit inventories contain 103 changed paths. Comparisons cover all available changed `Source/` paths, including API/native call sites, helpers, bytecode, interpreter, DFG, FTL, builtins and WebCore bindings; two exact Sony paths were unavailable as documented above. Sony retains `op_to_this` with ECMAMode and older call generation, not the wholesale refactor. Several files exactly match the pre-refactor/post-revert snapshots, but most differ through vendor/version changes.

**INCONCLUSIVE:** one cannot infer an exposed scope leak from absence of this reverted/open architectural replacement. Nor does the March Proxy patch establish the whole family is closed. The DFG iterator gap above must be evaluated independently. The [wiki](https://www.psdevwiki.com/ps4/WebKit_Bugs) was used to discover primary links, not as authority for patch status or firmware coverage.

## 4. Structured cloning: account for the whole object-pool change

[`010c6bdfb0cde0485d31f0260ab9a046fa9b8567`](https://github.com/WebKit/WebKit/commit/010c6bdfb0cde0485d31f0260ab9a046fa9b8567), Bug 265975, and original branch [`430d474531c0feb483cf5ffdf968e7dbdcf3ad4e`](https://github.com/WebKit/WebKit/commit/430d474531c0feb483cf5ffdf968e7dbdcf3ad4e) were compared with their parents. Both changed source files were inspected: `SerializedScriptValue.cpp` and `OptionsList.h`.

**CONFIRMED IN SOURCE:** the coordinated changes are represented, rather than just a renamed field:

1. Object reference graph indexing uses `m_objectPoolMap`; retained graph entries use `m_objectPool`.
2. Serializer scratch lifetime protection uses separate `m_keepAliveBuffer` at 2487.
3. Tagged `writeObjectReferenceIfDupe`, `addToObjectPool` and `addToObjectPoolIfNotDupe` helpers constrain graph accounting (1142–1188).
4. Map and Set serialization register graph objects once; iterators and the temporary map value go to keep-alive storage (2642–2692).
5. Primitive `readBigInt` does not append temporary primitive values to the object reference pool; boxed BigInt does register its wrapper (4215 onward; 4368).
6. Deserializer Array/Object/Map/Set entries use the tagged object-pool helpers (4851/4892/4929/4959).
7. Pool tag accounting and a serializer/deserializer comparison validator are present (887–902, 5010 onward).
8. The accompanying `OptionsList.h:240` option exists and defaults false. Validator call/implementation are under `ASSERT_ENABLED`, with complex-case, success and runtime-option guards. This diagnostic mechanism is not an unconditional release-build protection.

**INCONCLUSIVE:** whole-file and every serialization-case equivalence. Sony's file has serialization version 13; the compared upstream fixed file uses 15. There are older API/configuration/tag differences and many absent trace-only lines; those differences do not alone negate the core pool fix or establish a vulnerability. The two files are not byte-identical. Assertions/debug validation presence does not establish that production executes them. No malformed clone graph, crafted binary clone data, getter/prototype hooks or GC stress was used.

**NOT VERIFIED:** production binary correspondence, absence of other cloning bugs, or a remaining Relapse-compatible primitive on 14.10.

## 5. Can Sony's publication identify the 14.10 production browser?

| Evidence | Status and limitation |
| --- | --- |
| [Official WebKit listing](https://www.playstation.com/en-us/oss/ps5/webkit/) | **CONFIRMED IN SOURCE:** currently labels WebKit_1400 “14.00 -”, overlapping the preceding “12.00 - 14.00” range. Broad firmware association, not a per-build executable identity. |
| [Standalone JSC listing](https://www.playstation.com/en-us/oss/ps5/webkit-javascriptcore/) | **CONFIRMED IN SOURCE:** “8.00 -” listing; not a precise 14.10 component manifest. Standalone JSC-800 was not acquired here. |
| `Configurations/Version.xcconfig:24–29,64–65` | **CONFIRMED IN SOURCE:** 616.1.27.211.1, with generic source-version linker settings. No Sony firmware/build-to-object hash mapping in this file. |
| `UserAgentPlayStation.cpp:64,71` | **CONFIRMED IN SOURCE:** fixed AppleWebKit/605.1.15 and Version/17.0 tokens. Reported firmware comes through a separate platform value. |
| Root `ReadMe.md` | **CONFIRMED IN SOURCE:** generic upstream build instructions; no target build manifest in the inspected document. |
| Archive member-name inventory | **CONFIRMED IN SOURCE:** version/revision candidates mostly identify tests, third-party code or generic build templates. No exact production mapping was identified by this inventory and inspected metadata. This is not an exhaustive content search of every archive file. |
| Production configuration, component hashes and source provenance | **NOT VERIFIED:** no signed per-component firmware manifest, matching executable build ID/hash, compiler configuration or reproducible build correspondence obtained. |

**INCONCLUSIVE:** exact production patch state. Sony provides enough to associate the publication broadly with 14.x, but the reviewed metadata is insufficient to verify which of these paths is compiled into the particular 14.10 browser executable. Selectively backported files also preclude deriving one upstream revision from the component version.

## 6. Ranked remaining questions

Ranking is evidence-gathering value, not exploit probability.

| Rank | Question | Existing evidence quality | Highest-value safe action |
| --- | --- | --- | --- |
| 1 | Which exact WebKit/JSC build and configuration shipped in 14.10? | Strong publication provenance; weak executable correspondence | Seek an official per-component manifest/build mapping or authorized accessible binary identity. Compare hashes/build metadata offline if supplied; do not assume encrypted PUP content is readable. |
| 2 | Does the shipped font lifetime path retain the same ownership behavior? | High confidence in both missing source safeguards; no target lifetime evidence | Obtain target-corresponding source/build confirmation; audit adjacent ownership/callback code statically. Do not run reentrancy/crash tests. |
| 3 | What limits bound metadata generation in the shipped parser? | High confidence that the entire five-file named fix is absent in source | Statically trace existing instruction/profile/count caps and build-specific metadata sizes; use small mathematical fixtures, not huge target programs. |
| 4 | Is the old DFG iterator path compiled/enabled? | Direct source gap, contrary-to-exposure default build flags | Verify configuration through authorized build records. Do not infer JIT status from timing or stress the optimizer. |
| 5 | Are older-version clone tags and vendor branches consistently pool-accounted? | Core fix represented in both changed source files; no exact whole-file equivalence | Audit matching serializer/deserializer tags and configuration guards offline; source-version differences are not automatically bugs. |

No live bridge task available here can authenticate a native component revision or prove these memory-safety paths safe. API presence and successful ordinary operations are not patch oracles. **NOT VERIFIED:** current online client state this phase; the bridge was not contacted and historical session results were not represented as fresh. A future normal-path clone conformance test could describe standards behavior, but cannot settle the missing production mapping and was therefore not repeated or added now.

## Reproduction, verification and preservation

The evidence JSON records immutable raw-source URLs for fixed and parent files plus source hashes and selected numbered excerpts. Authorized local files are under `derived/patch-family-20261020/sony/`; fixed/parent snapshots are under `upstream/<commit>/`; generated diffs are under `diffs/<commit>/`. Recompute SHA-256 with `Get-FileHash -Algorithm SHA256`, or use Python's standard-library `hashlib`. Source comparisons are static; no dependencies or engine builds are needed.

The acquisition scripts and intermediate records remain in ignored local research storage. Committed evidence contains provenance and analysis, not firmware binaries, credentials or executable triggers. Fresh verification checks all recorded local source hashes, fixed/parent comparisons, primary-fix path coverage, selected source excerpts and report consistency. No product tooling changed, so browser/unit regression tests were not rerun and no previous test count is presented as new. Changes are committed locally only; no push is authorized.
