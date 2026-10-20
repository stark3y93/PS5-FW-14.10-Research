# Public research index

Snapshot date: 2026-10-20 (Europe/London). The machine-readable [source ledger](sources.json) pins each upstream HEAD to a commit. Search it with `rg '14\.10|parser|licence|firmware' research/` or parse the JSON. This index records repository evidence, not executable instructions or a claim that an exploit works on firmware 14.10.

## Evidence rules

- **Observed in source**: a file, tree entry, licence, or test present at the pinned commit. This proves what the repository contains, not that code works on a PS5.
- **Author claim**: a README or committed report states a hardware result. Logs and probe output may support it, but we have not independently authenticated the console, firmware, or capture chain.
- **Inference**: a conclusion drawn from repository evidence. It must name its premise and remain open to revision.
- **Unknown**: evidence needed for a compatibility conclusion is absent.

The [firmware toolkit's own 14.10 provenance](../notes/provenance.md) establishes only the identity of a locally analysed official update wrapper. Wrapper measurements cannot establish exploit compatibility, kernel state, or the security posture of a running console.

## Repository map

| Project | Pinned revision | Licence / contribution policy | Capability and firmware evidence | 14.10 assessment |
| --- | --- | --- | --- | --- |
| [PS5Dev/PS5-UMTX-Jailbreak](https://github.com/PS5Dev/PS5-UMTX-Jailbreak) | [`2cf6778`](https://github.com/PS5Dev/PS5-UMTX-Jailbreak/tree/2cf6778ebe89ff35255e1c228826d0d2155e9d2a) | Unlicense; no `CONTRIBUTING.md` in pinned tree | Host and JavaScript code; README lists 1.00–5.50 variants and says ≥6.00 needs a different WebKit entry | No support shown; README explicitly excludes ≥6.00 |
| [PS5Dev/PS5SDK](https://github.com/PS5Dev/PS5SDK) | [`a2e03a2`](https://github.com/PS5Dev/PS5SDK/tree/a2e03a2a0231a3a3397fa6cd087a01ca6d04f273) | GPL-2.0; README invites pull requests; no `CONTRIBUTING.md` | SDK headers, CRT, CMake, examples; README's firmware-specific kernel helper list ends at 4.51 | No 14.10 offsets or runtime support established |
| [Gezine/Luac0re](https://github.com/Gezine/Luac0re) | [`6fa8db6`](https://github.com/Gezine/Luac0re/tree/6fa8db6c021e1ae01864455e03e9c86aa5d33d66) | MIT; no `CONTRIBUTING.md` | Lua-based mast1c0re variation; README describes userland JIT capability and notes one related payload requires ≤12.00 | README's “latest” wording is not a pinned 14.10 compatibility test |
| [ntfargo/Relapse-Exploit](https://github.com/ntfargo/Relapse-Exploit) | [`dd8e4e0`](https://github.com/ntfargo/Relapse-Exploit/tree/dd8e4e0914c5e9d066ee1f9b056be76cb992c8e0) | MIT; no `CONTRIBUTING.md` | Web host and JavaScript chain; README states 7.00–13.60 | 14.10 outside the stated range |
| [zecoxao/ps5-pup-unpacker](https://github.com/zecoxao/ps5-pup-unpacker) | [`005cccc`](https://github.com/zecoxao/ps5-pup-unpacker/tree/005cccc908142c35ab7280e7f9eef8d5203c21e0) | No root licence or contribution guide in pinned tree; bundled zlib has separate notices | C++ utility for **previously decrypted** update blobs; README excludes nested filesystem unpacking | No firmware range stated; cannot process our encrypted/opaque inner PUP on this evidence |
| [pastawithpesto/PS5-14.10-Jailbreak-Research](https://github.com/pastawithpesto/PS5-14.10-Jailbreak-Research) | [`ea1beed`](https://github.com/pastawithpesto/PS5-14.10-Jailbreak-Research/tree/ea1beed081adfdbebd887db558358c753633b575) | No root licence; `CONTRIBUTING.md` contains a heading only | README, documentation and offline host test fixtures claim 14.10 browser probes; README describes candidate bugs and unresolved stages | 14.10 **research claims**, not an independently verified jailbreak or complete chain |
| [ZigZagBoi1/PS5-14.10-Research](https://github.com/ZigZagBoi1/PS5-14.10-Research) | [`2bfb6b5`](https://github.com/ZigZagBoi1/PS5-14.10-Research/tree/2bfb6b54940dfbd18d05b2712d723b0b4cfd0049) | No root licence; [contribution guide](https://github.com/ZigZagBoi1/PS5-14.10-Research/blob/2bfb6b54940dfbd18d05b2712d723b0b4cfd0049/CONTRIBUTING.md) requests forks, tests and PRs | Extensive Lua probes, saved results and offline audit tools. README explicitly says no demonstrated 14.10 kernel read/write or full exploit | Direct evidence of a research corpus; device claims remain author-reported |

All seven GitHub repositories existed on the snapshot date. Their full commit hashes, primary links, limitations, evidence quality and potential engineering contributions are in `sources.json`. GitHub's public metadata supplied licence identifiers where present; absence of a top-level `LICENSE` means no general reuse permission should be inferred. File-tree inspection found no dedicated test directory in the first five projects, although `ps5-pup-unpacker` bundles zlib's own tests; that is a discovery lead, not proof that no tests exist elsewhere.

## Research boundaries and next use

These projects cover distinct layers: outer update-wrapper analysis (this repo), decrypted inner package handling, SDK/build tooling, browser or Lua userland entry, and kernel-facing research. Compatibility at one layer does not establish another. The two 14.10 community repos warrant careful reading of their raw evidence and offline test tools, but neither can be treated as independent proof of a working 14.10 jailbreak.

Use [open questions](questions.md) before starting new work. Proposed improvements should target offline parser correctness, reproducible builds, evidence provenance and documentation. Do not import third-party source into this repository until its exact licence and purpose are reviewed.
