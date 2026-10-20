# Cross-version SLB2 comparison: provenance gate and current result

## Research question and decision rule

Does the 14.10 wrapper's second 512-byte block, with nonzero runs at relative offsets `[0,32)` and `[480,512)`, recur in other **official PS5 update packages**? A package enters the real comparison only when a Sony-controlled source binds an exact version to its download URL, the downloaded length matches that source, and the full-file SHA-256 matches the Sony URL digest. A filename, third-party table, release date, or sample label alone is insufficient. The comparison command verifies bytes against caller-supplied hashes but does **not** authenticate version labels or Sony provenance.

## Official source audit, 20 October 2026

| Version | Sony evidence | Package status |
| --- | --- | --- |
| `26.06-14.10.00` | [Current Sony support page](https://www.playstation.com/en-gb/support/hardware/ps5/system-software/) links its update package; [Sony release notes](https://www.playstation.com/en-gb/support/hardware/ps5/system-software-info/) identify the version. The live [Sony US update list](http://fus01.ps5.update.playstation.net/update/ps5/official/tJMRE80IbXnE9YuG0jzTXgKEjIMoabr6/list/us/updatelist.xml) identifies `system_pup` version `14.10.00.00`, label `26.06-14.10.00.03-00.00.00.0.1`, image length `1,261,408,256`, and the same `sys_C17384946DF6E5C85B2D72CBEEE2057B165BF90279D9E2A86D527D0778CDAAF6` digest as the support-page link. The live Sony Japan list named the same digest and version. | Included. Existing ignored file length and SHA-256 match. |
| `26.06-14.00.00` | Listed as a previous release in Sony's [release notes](https://www.playstation.com/en-gb/support/hardware/ps5/system-software-info/). | Excluded: the current Sony download page and live update lists do not identify an exact 14.00 update-package URL. |
| `26.05-13.60.00` | Listed as a previous release in the same Sony release notes. | Excluded for the same reason. |
| Newer than 14.10 | Sony's current release notes and download page list 14.10 as latest. | No verified newer official update available in the checked sources. |

The US list was fetched directly from Sony at 11:20 UTC. It contained one `system_pup` entry, for 14.10. The Japan list reported the same version and digest. The list endpoint used HTTP, so its contents alone are not a cryptographic authenticity proof; the HTTPS support-page link, matching URL digest, length, and local hash provide independent consistency checks. No Sony package was downloaded or overwritten during this phase. Historical manifests circulating outside Sony's current endpoints were not used as version evidence because the study requires official Sony sources only.

## 14.10 measurements, not a cross-version result

The existing original package was rehashed before and after the read-only map: SHA-256 `C17384946DF6E5C85B2D72CBEEE2057B165BF90279D9E2A86D527D0778CDAAF6`. Its size is `1,261,408,256` bytes and the SLB2 block count is `2,463,688`. The parsed SLB2 header is 32 bytes, with one 48-byte entry record and 432 zero bytes remaining in the first block. The entry begins at byte 1,024 (block 2), spans 1,261,406,781 bytes, ends at byte 1,261,407,805 (offset 61 within its last 512-byte block), and is followed by 451 zero bytes. The complete `[512,1024)` pre-entry block contains 448 zero bytes and two 32-byte nonzero runs at `[512,544)` and `[992,1024)`. Its empirical entropy is 1.2530 bits/byte. These observations reproduce [the prior neighborhood report](wrapper-neighborhood-14.10.md); they do not identify the purpose of those runs.

**Cross-version conclusion: inconclusive.** Exactly one version satisfies the provenance gate. There are no measured differences or stable cross-version patterns to report, and the two 32-byte runs have **not** been observed in another verified version. The pattern is a reproducible observation on 14.10, not a proven signature, checksum layout, encryption marker, format change, or jailbreak indicator.

## Code, validation, and limits

`ps5fwlab compare` accepts two or more distinct `--package SAMPLE_ID FILE SHA256 EXPECTED_SIZE` arguments. It checks each supplied length and hashes each whole file before and after mapping, validates the SLB2 table, and reads at most two 512-byte edge samples per region. It reports numeric header fields, entry records, start blocks, end alignment, complete pre-entry run intervals, entropy, zero counts, and final padding. It marks run comparison **inconclusive** if any pre-entry gap is not completely measured. `SAMPLE_ID` is explicitly an unauthenticated label; researchers must establish version provenance separately. Full reports belong in ignored `derived/`; Sony bytes and extracted content are never written by the tool.

The baseline suite passed **29/29** with this checkout's `src` selected. The extended suite passed **36/36** with `python -S -m unittest discover -s tests -v`. New synthetic cases cover matching, differing, and incompletely measured run patterns; distinct hash requirements; incorrect hashes; multiple entry lengths; overlapping entries; inconsistent block counts; and file preservation. Existing parser tests cover invalid offsets, truncation, header capacity and range bounds. The review of open PRs #7 and #8 found no package upload or execution path. PR #7's SHA-seeded sample is deterministic, but its statistical benchmark is model-conditional rather than a random-sampling guarantee, as its note says. PR #8's original source-preservation test compared an in-memory input with itself; this branch strengthens it to compare the on-disk file after mapping.

## Best next PC-only experiment

Seek Sony-controlled, version-bound historical update metadata for **14.00** and **13.60**. If obtained, download only the matching Sony-hosted update files into separate ignored paths, verify their sizes and SHA-256 against Sony metadata, then run the fixed comparator without changing the protocol. Only then can the two-run pattern be classified as recurrent or version-dependent. Firmware interior decryption and console behavior remain outside this experiment.
