# PS5 14.10 WebKit provenance

**Conclusion: UNKNOWN for the exact firmware executable.** A Sony-published source version and two exact source-file matches were established. A complete 14.10 browser revision or patch state was not.

## Manufacturer evidence

On 20 October 2026 Sony's [PS5 WebKit source listing](https://www.playstation.com/en-us/oss/ps5/webkit/) linked `WebKit_1400.zip` under “14.00 -”. The preceding bundle is labeled “12.00 - 14.00”; the overlapping endpoint and open range do not identify individual production component builds. The [official archive URL](https://www.playstation.com/content/dam/global_pdc/en-us/external-resources/oss/PS5/webkit/WebKit_1400.zip), listing-page byte hash, observed HTTP metadata and selected member hashes are recorded in [WEBKIT_SOURCE_EVIDENCE.json](WEBKIT_SOURCE_EVIDENCE.json).

The archive reports 1,637,794,253 bytes. The acquisition transferred 73,444,196 bytes through validated HTTP ranges, including ZIP directory metadata and eight selected members. `ZipFile` validated each extracted member's CRC. No full archive SHA-256 was measured in this acquisition; the digest recorded on another branch was not represented as a newly verified whole-archive result.

| Published file | SHA-256 / observation | What it establishes |
|---|---|---|
| `Source/WebCore/css/CSSFontFace.cpp` | `047110c865310422c0ef77c05268841b1ac982bc22120e8c8e265539c713f3ab` | Exact match to the file at upstream `0e722583a4d695c7b25f384c61fbf5b59b4c3146`; copied-client callbacks are unconditional. |
| `Source/WebCore/css/FontFace.cpp` | `82b68a296b73840857f0947ae533748d86a8f52248d03cd3f4f06176e56ed50a` | Exact match to that upstream file; `loadForBindings` lacks the temporary backing pin. |
| `Configurations/Version.xcconfig:24-28` | `2c2f5d80b270c69877aaf5bb075307e0b63d5227ca508e8d2474ea42336f5307`; version `616.1.27.211.1` | Published source version; also matches the pinned upstream file. It is not a compiled 14.10 build ID. |
| `Source/cmake/OptionsPlayStation.cmake:206-208` | JIT, FTL JIT, and DFG JIT default OFF; file differs from the pinned upstream version. | Sony source changes and build defaults; final production overrides remain unknown. |
| `Source/WebCore/platform/playstation/UserAgentPlayStation.cpp:61-71` | `050f6eb12ea89016954e1a5e6927b641d40a590386ea410f88512585ad09eff3`; hardcoded browser tokens | Explains why user-agent strings cannot identify the source revision. This file also differs from the pinned upstream version. |

Five of the eight selected files match the pinned upstream revision: the two implementation files, FontFace.h, CSSFontFaceSet.cpp and the version file. Three differ: platform options, user-agent code and CSSFontFace.h. In the last file, the destructor declaration omits upstream's `virtual`; no ABI or object-layout equivalence is inferred. These mixed results do not establish a whole-tree commit. The separate [Sony JavaScriptCore listing](https://www.playstation.com/en-us/oss/ps5/webkit-javascriptcore/) still links `JSC-800.zip` under “8.00 -”; that older standalone archive must not be substituted for JSC embedded in the WebKit bundle without component-specific evidence. The current JSC archive was not downloaded again during this phase.

## User agent is not an engine revision

The published Sony port obtains the system software name/version from platform environment data but returns a fixed `605.1.15` browser token and emits `Version/17.0 Safari/605.1.15`. The saved desktop research log `results/beacon-logs/v480-fixed-literal-results.txt:1` reports the same browser tokens alongside `PlayStation 5/14.10`. That observation is compatible with the published port, but it does not prove the compiled engine's age, source revision or fix status. A source/binary hash or authenticated build mapping is required.

## Firmware and binary examination

The local `D:\PS5UPDATE.PUP` was rehashed: 1,261,408,256 bytes, SHA-256 `c17384946df6e5c85b2d72cbeee2057b165bf90279d9e2a86d527d0778cdaaf6`. The existing bounded parser confirms the outer SLB2 metadata. The inner package remains opaque; no browser executable was extracted, decrypted or compared. Wrapper size, dates and source ZIP version strings do not reveal its WebKit functions.

The inspected local repository/artifacts and public manufacturer sources supplied no authorized 14.10 browser executable, symbol file, signed component manifest, or exact WebKit Git revision for `26.06-14.10.00`. Sony's [14.10 release notes](https://www.playstation.com/en-gb/support/hardware/ps5/system-software-info/) describe security fixes without a component revision or CSSFontFace patch diff. This is a bounded search result, not a claim that such evidence cannot exist.

## Attribution ladder

1. **Verified:** published Sony bundle association with the “14.00 -” range.
2. **Verified:** sampled source bytes, old function shapes, source version and vendor platform changes.
3. **Unestablished:** exact source-to-browser binary mapping for 14.10, including backports and production configuration.
4. **Unestablished:** a CSSFontFace memory fault on authenticated 14.10 hardware or a target-matched engine build.
5. **Unestablished:** a useful browser primitive, sandbox transition, kernel vulnerability or hypervisor consequence from this candidate.

The source lead is stronger than a generic upstream analogy. The final firmware classification nevertheless remains **UNKNOWN**.
