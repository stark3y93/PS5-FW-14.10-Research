# Source coverage and extraction ledger

Snapshot: 2026-10-20. Inspected repositories are pinned to the commits listed below. "Fully extracted" means the bounded repository-level scope recorded in `coverage`, not an exhaustive audit of all code. No third-party exploit or payload code was run.

| Repository | Inspected commit | License recorded | Coverage reviewed |
|---|---|---|---|
| [PS5Dev/PS5-UMTX-Jailbreak](https://github.com/PS5Dev/PS5-UMTX-Jailbreak/tree/2cf6778ebe89ff35255e1c228826d0d2155e9d2a) | `2cf6778ebe89ff35255e1c228826d0d2155e9d2a` | Unlicense | fully extracted at README/source-tree level |
| [PS5Dev/PS5SDK](https://github.com/PS5Dev/PS5SDK/tree/a2e03a2a0231a3a3397fa6cd087a01ca6d04f273) | `a2e03a2a0231a3a3397fa6cd087a01ca6d04f273` | GPL-2.0 | fully extracted at README/offset-table level |
| [Gezine/Luac0re](https://github.com/Gezine/Luac0re/tree/6fa8db6c021e1ae01864455e03e9c86aa5d33d66) | `6fa8db6c021e1ae01864455e03e9c86aa5d33d66` | MIT | partially extracted; README and project scope reviewed |
| [ntfargo/Relapse-Exploit](https://github.com/ntfargo/Relapse-Exploit/tree/dd8e4e0914c5e9d066ee1f9b056be76cb992c8e0) | `dd8e4e0914c5e9d066ee1f9b056be76cb992c8e0` | MIT | fully extracted for README, version gate and license |
| [zecoxao/ps5-pup-unpacker](https://github.com/zecoxao/ps5-pup-unpacker/tree/005cccc908142c35ab7280e7f9eef8d5203c21e0) | `005cccc908142c35ab7280e7f9eef8d5203c21e0` | No root license found at pinned tree | partially extracted; README, reader and integer widths reviewed |
| [pastawithpesto/PS5-14.10-Jailbreak-Research](https://github.com/pastawithpesto/PS5-14.10-Jailbreak-Research/tree/ea1beed081adfdbebd887db558358c753633b575) | `ea1beed081adfdbebd887db558358c753633b575` | README states MIT; no root LICENSE file at pinned tree, so a formal reuse grant was not established | partially extracted; README, visible reports and evidence limits inspected; no code executed |
| [ZigZagBoi1/PS5-14.10-Research](https://github.com/ZigZagBoi1/PS5-14.10-Research/tree/2bfb6b54940dfbd18d05b2712d723b0b4cfd0049) | `2bfb6b54940dfbd18d05b2712d723b0b4cfd0049` | No root license found at pinned tree | partially extracted; README, progress report and license status inspected; code/tests not run |
| [nikosradio/ps4tools](https://github.com/nikosradio/ps4tools/tree/2aabe4da09ba14c41f3a0d8516aa756742ef4688) | `2aabe4da09ba14c41f3a0d8516aa756742ef4688` | GPL-2.0 | partially extracted; SLB2 structure and extraction loop reviewed |
| [zecoxao/ps5-pup-decrypt](https://github.com/zecoxao/ps5-pup-decrypt/tree/290f5dd216b6878223457f51b32127acc480964a) | `290f5dd216b6878223457f51b32127acc480964a` | No root license found at pinned tree | partially extracted; README prerequisites reviewed |
| [kmeps4/PSFree](https://github.com/kmeps4/PSFree/tree/368d82aa40d3017c220757ce315761adb5f06678) | `368d82aa40d3017c220757ce315761adb5f06678` | AGPL-3.0 | fully extracted for public version claim and scope |
| [soniciso1/relapse](https://github.com/soniciso1/relapse/tree/112dbe5949e9c3de923bb0909289c58a9c082151) | `112dbe5949e9c3de923bb0909289c58a9c082151` | No root license found at pinned tree | partially extracted; README and file tree reviewed |
| [ps5-payload-dev/sdk](https://github.com/ps5-payload-dev/sdk/tree/f5d40f02770e9b0001dd9e18056eca70b3da8b40) | `f5d40f02770e9b0001dd9e18056eca70b3da8b40` | GPL-3.0; some BSD headers noted | partially extracted; scope and prerequisites reviewed |
| [ChendoChap/PS5-Webkit-Execution](https://github.com/ChendoChap/PS5-Webkit-Execution/tree/ad157f5c074818658ca842301837fab43e08dc00) | `ad157f5c074818658ca842301837fab43e08dc00` | No root license found at pinned tree | fully extracted as historical write-up; no code run |
| [ntfargo/CSSFontFace-Exploit](https://github.com/ntfargo/CSSFontFace-Exploit/tree/221baa6e7349b96a6fd299808a25a4178e47741c) | `221baa6e7349b96a6fd299808a25a4178e47741c` | MIT | partially extracted; README range and license reviewed |
| [PS5Dev/Byepervisor](https://github.com/PS5Dev/Byepervisor/tree/57204cbd7bd26ed4623634d52b0f60f40d630087) | `57204cbd7bd26ed4623634d52b0f60f40d630087` | Unlicense | fully extracted at README/architecture-claim level |
| [PS5Dev/Byepervisor-Reborn](https://github.com/PS5Dev/Byepervisor-Reborn/tree/ea04f7132b837087f552c57261cb800481a3a910) | `ea04f7132b837087f552c57261cb800481a3a910` | Not asserted in this ledger; license file requires recheck before code reuse | partially extracted; README compatibility claims reviewed |
| [Cryptogenic/PS5-IPV6-Kernel-Exploit](https://github.com/Cryptogenic/PS5-IPV6-Kernel-Exploit/tree/4d4c5b25eb74ba47ca136b7827a8cffabc522736) | `4d4c5b25eb74ba47ca136b7827a8cffabc522736` | License status not rechecked in current source index | partially extracted; README version claims reviewed |
| [MewX/ps5-official-firmware-list](https://github.com/MewX/ps5-official-firmware-list/tree/83b0b510580bdbf3a2b77c05ccc7566e887be60d) | `83b0b510580bdbf3a2b77c05ccc7566e887be60d` | Not verified; no reuse permission assumed | two pinned XML metadata rows reviewed; not Sony firmware attestation |

## Extraction state

- Fully extracted for the bounded claim noted in `coverage`: 6 repository records.
- Partially extracted by README, visible source paths, compatibility tables, or license metadata: 12 repository records.
- Not studied in this snapshot: exhaustive file-by-file review and execution/testing of third-party exploit projects; no third-party payloads were run.
- Each repository record preserves claimed firmware range and the source evidence categories. A reported/tested range is not transferred to other firmware versions.

## Existing knowledge baseline

PR #13 source index commit `da5114413e3cadcc34dcebcc4c1b8c9ea93073c2` indexed 7 repositories and classified 18 evidence URLs. The unified catalog retains those pinned records and now indexes 18 repositories, 27 technical/vendor/support documents, source-linked questions, and upstream CVE records. Coverage includes Sony release and source listings, source-version scope, WebKitGTK advisories, FreeBSD advisories, Sony's version-viewing instructions, and pinned community reports. None establishes exact Sony component-to-build vulnerability mapping for 14.10.

The additional repository records primarily improve indexing of earlier work, plus the MewX historical update-list metadata; they should not be described as new technical discoveries. The later PR #14 commits add distinct FreeBSD jail CVE records, source provenance and question evidence, and three bounded author-reported browser findings. The PR #15 additions retain Sony archive HEAD metadata and newer WebKitGTK advisory scope. The two public 14.10 community repositories add author-reported device research claims, but the catalog treats them as unverified rather than independent evidence.

## Unified integration status

Branch `research/unified-evidence-2026-10-20` starts from `origin/main` (`46ebfc78eec7d863af1d73003681b1dc0fc44944`) and merges PR #13 head `da5114413e3cadcc34dcebcc4c1b8c9ea93073c2`, `research/vulnerability-lab` (`b4f7b456789c712fde8aa345879d7139981fb8c8`), and `research/max-intelligence-2026-10-20` (`c25f02c3ad9147400dd23184c830d1b70d14335e`), and the four later PR #14 commits through `8cf91e8` using merge commits, including PR #14 final head `8cf91e8` (merge commit `1bc71d7`). This preserves the contributing commit histories. The publication-audit worktree remains separate; no research contributor worktree was edited or rebased. Merge commits: `5608dcd`, `240ac96`, and `a7051bd`.

The integration adds no firmware archive, exploit payload, credential, or copied third-party implementation. The catalogue contains URLs, pinned public repository commit IDs, source/license status, scope-labelled findings and generated database/dashboard instructions. Sony's official WebKit and JavaScriptCore pages link to version labels `WebKit_1400` (14.00 onward) and `JSC-800` (8.00 onward). On 2026-10-20, HTTP HEAD returned archive lengths of 1,637,794,253 and 1,369,859,528 bytes, respectively, plus Last-Modified dates and ETags recorded in `catalog.json`. ETags are validators, not hashes. Both archives were subsequently downloaded, SHA-256 hashed and inspected in the source-validation phase; see `notes/source-archive-analysis-2026-10-20.json`. Exact 14.10 source/build correspondence remains unknown.

Current WebKitGTK WSA-2026-0005 and WSA-2026-0006 were added as upstream-only source records. WSA-2026-0006 (2026-09-29) lists CVEs across WebKitGTK/WPE and bundled components; each entry's product/version scope must be read individually. These advisories do not establish applicability to PlayStation's fork. CVE-2026-43715 is confirmed in WSA-2026-0004/Red Hat as a WebKitGTK use-after-free with upstream affected-version scope, but the cited 14.10 CSSFontFace claim's equivalence and Sony applicability remain unverified. WebKit Bugzilla 313577 returned access denied during this check, so no source patch/commit was independently mapped from that bug.
