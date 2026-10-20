# WebKit target compatibility: firmware 14.10

Audit date: 20 October 2026. **Production executable compatibility remains UNKNOWN.** This report adds source evidence to PR #21; it does not replace its original measurements.

## Strongest mapping and its limit

[Sony's current PS5 WebKit release list](https://www.playstation.com/en-us/oss/ps5/webkit/) associates `WebKit_1400.zip` with an open-ended **14.00 -** label. This is positive vendor evidence that the source is relevant to the 14.xx family, and makes CSSFontFace a plausible target lead. The adjacent **12.00 - 14.00** label overlaps. Neither identifies a signed 14.10 executable, all private changes, production build options, or an exact binary/source correspondence. [Official 14.10 release notes](https://www.playstation.com/en-gb/support/hardware/ps5/system-software-info/) identify `26.06-14.10.00` and generic security changes without component revisions. No newly inspected record supplies the missing correspondence.

The earlier sampled version file declares `616.1.27.211.1`, while the published PlayStation UA implementation hardcodes `605.1.15` and `Version/17.0`. Those browser strings cannot date the engine. The platform firmware portion comes from a separate environment field. [Previous measured hashes and source lines](WEBKIT_SOURCE_EVIDENCE.json) remain preserved. API fingerprints likewise cannot identify backports.

## New counterexample to whole-build version inference

Four additional members of the [official archive](https://www.playstation.com/content/dam/global_pdc/en-us/external-resources/oss/PS5/webkit/WebKit_1400.zip) were independently retrieved using validated HTTP ranges and ZIP CRC checks. Archive size: **1,637,794,253 bytes**; this acquisition transferred **73,421,902 bytes**, principally ZIP-directory data. No full-archive hash was measured. Exact paths, member SHA-256 values, source URLs and selected line evidence are in [PHASE4_SOURCE_EVIDENCE.json](PHASE4_SOURCE_EVIDENCE.json).

| Published member | New observation | Consequence |
|---|---|---|
| `Source/WebCore/Modules/streams/TransformStream.cpp` | Lines 115–119 reject a wrong result count. Lines 121–127 check the readable/writable casts before line 129 accesses wrapped objects. | Both central checks from the public type-confusion fix are present in Sony's source. |
| `Source/JavaScriptCore/bytecode/UnlinkedMetadataTable.cpp` | Byte-identical to upstream `0e722583a4d695c7b25f384c61fbf5b59b4c3146`; line 109 uses an unsigned offset; lines 127–129 align and add the count/size product without the later checked arithmetic. | A concrete old source pattern is present in the bundle; actual overflow reachability and production inclusion remain unknown. |
| `Source/JavaScriptCore/bytecode/UnlinkedMetadataTable.h` | Lines 113–118 return table total size; line 130 defines `Offset32` as `uint32_t`. | Establishes the published representation, not a runtime allocation or write. |
| `Source/JavaScriptCore/bytecode/MetadataTable.h` | Lines 98 and 109–128 consume stored offsets. | Supplies follow-on code context; does not establish that attacker input reaches overflow. |

Sony's TransformStream file differs from the 2023 baseline **only by the two validation safeguards and associated error returns**. Its API spelling differs from current main, so the whole file is not byte-identical to the 2026 mainline fix. This is direct evidence of selective changes in an otherwise old source lineage. It is therefore unsafe to label every component vulnerable merely because the version file is old. CSSFontFace's missing safeguards still require their own target mapping; the TransformStream checks do not prove the font fix exists.

## Candidate reassessment

| Candidate | Primary advisory / patch | Published source assessment | 14.10 assessment / limitation |
|---|---|---|---|
| CSSFontFace / CVE-2026-43715 | [GTK/WPE advisory](https://webkitgtk.org/security/WSA-2026-0004.html), lifetime [f3d61dae](https://github.com/WebKit/WebKit/commit/f3d61dae1b61dfbd2fc0b01196b63f8769bca77e), membership [f1fff08a](https://github.com/WebKit/WebKit/commit/f1fff08a99d77bac49c2500ece3fdcfac06c8f1c) | Prior exact source comparison shows both absent. Lifetime pin fixes the security issue; membership guard also addresses the separate stress assertion. | Plausible source lead, high confidence in source observation; **UNKNOWN target impact**. No target heap fault reproduced. |
| TransformStream / CVE-2026-43705 | Same advisory, Bugzilla 314528; [8fd92b1021d310b2580eb3ac7913911eb14dc476](https://github.com/WebKit/WebKit/commit/8fd92b1021d310b2580eb3ac7913911eb14dc476) | Sony already has the size/type checks. **Specific unchecked-result hypothesis contradicted for this published file.** | Do not claim a vulnerable 14.10 implementation. Binary state unknown; no unsafe iterator test executed. |
| UnlinkedMetadataTable / CVE-2026-64784 | [GTK/WPE advisory](https://www.webkitgtk.org/security/WSA-2026-0006.html), Bugzilla 317632; [97df94ead028cddcfc21e48ec6f2f72d25ec1662](https://github.com/WebKit/WebKit/commit/97df94ead028cddcfc21e48ec6f2f72d25ec1662) | New comparison establishes the old unsigned arithmetic; upstream adds checked offsets, alignment overflow detection and failure propagation to the bytecode generator. | Stronger source lead than before. Exact build, limits, reachable counts, opcode size, allocation outcome and memory fault remain unverified. Corrected V480 zero hits remain a negative result for its specific claim. JIT OFF does not by itself exclude bytecode-generation arithmetic. |
| UMTX / CVE-2024-43102 | [FreeBSD advisory](https://www.freebsd.org/security/advisories/FreeBSD-SA-24:14.umtx.asc); [public PS5 implementation](https://github.com/PS5Dev/PS5-UMTX-Jailbreak/tree/2cf6778ebe89ff35255e1c228826d0d2155e9d2a) | Upstream reference-count race is real; the public PS5 project's supported chain is for older firmwares. No Sony 14.10 kernel function compared. | **No 14.10 support established.** Calling a syscall or creating a thread is not evidence for this race. |

The advisories' affected ranges are **GTK/WPE before 2.52.5** for the first two candidates and **before 2.54.0** for the metadata issue. They are not Sony firmware ranges. Introducing revisions and a universal affected-fork range were not established. The upstream regression programs were not run; no engine build was installed. Pure arithmetic/source comparison cannot establish a usable primitive.

## Reproduce the offline comparisons

Use authorized local source members and the exact pinned revisions recorded in the JSON. The existing generic comparison records SHA-256 and a diff:

```powershell
python -S tools/ps5_research.py --compare E:\authorized-source\old\TransformStream.cpp E:\authorized-source\sony\TransformStream.cpp --output derived\transform-comparison-new.json
python -S tools/ps5_research.py --compare E:\authorized-source\old\UnlinkedMetadataTable.cpp E:\authorized-source\sony\UnlinkedMetadataTable.cpp --output derived\metadata-comparison-new.json
```

Those example paths must be replaced with files you possess. No source/binary extraction from the console is proposed. Public archive members stayed in ignored `derived/`; this PR publishes hashes, bounded evidence and analysis only.
