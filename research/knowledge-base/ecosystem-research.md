# PS5 ecosystem and compatibility review — 2026-10-20

This snapshot expands the pinned source catalog across browser/kernel research, Linux boot, graphics, native homebrew, application management, Steam/Wine, SDKs, and host-side translation/emulation. Repository metadata and default-branch commit pins were checked against GitHub on 2026-10-20. Counts describe indexed records, not newly verified vulnerabilities.

## Findings relevant to 14.10

- The current `ps5-linux-loader` README enumerates selected Phat/Slim firmware versions from 3.00 through 7.61 and 13.00, 13.20, and 13.60. The Pro row lists 13.60. It does not list 14.10. These are maintainer-published compatibility claims, not tests performed by this project. See the [pinned loader README](https://github.com/ps5-linux/ps5-linux-loader/blob/62020f57356375acb713ca5bfc3749c0fb209546/README.md).
- `pLinux5-NG` is a concrete documentation conflict: its project heading describes 8.xx–13.60, while a prominent status note says only 13.20 is currently supported. The matrix preserves both statements and marks the broad range contradicted as a support claim. See the [pinned README](https://github.com/pLabs5/pLinux5-NG/blob/978cfb3a1ff1dd5e6fc6e776c5aae3ed8c5770fd/README.md).
- No reviewed project makes a supported or independently reproduced 14.10 exploit, homebrew, Linux, or graphics claim. The two existing 14.10-targeted community records remain author-reported. This absence does not establish that a technique is patched or impossible.
- Sony’s 14.10 release record in the existing knowledge base reports unspecified security fixes; it names no component or CVE. The newly indexed homebrew projects do not resolve that Sony component/build mapping.

## Curated project additions

Fourteen new GitHub sources are now pinned in `ecosystem.json`; 14 more existing records are surfaced as ecosystem projects without duplicating their source records. Each source row records its repository URL, inspected commit, GitHub SPDX metadata where available, license caveat, research role and review coverage. The searchable SQLite view includes commit and license fields, check date, source credibility notes, and citations.

| Area | What the primary project source supports | Limits for this research |
|---|---|---|
| Linux loader and images | `ps5-linux-loader`, image build, kernel patches and tools form a distinct Linux-on-console stack. Current loader README has explicit old and 13.00/13.20/13.60 entries. | Does not establish 14.10 support, nor justify running an exploit. Image and patch repositories have no SPDX license declaration in GitHub metadata; no code is reused. |
| High-firmware Linux | `pLinux5-NG` describes reuse of the loader boot path and a different high-firmware path; its own current-status statement narrows support to 13.20. | The project is WIP. No test or execution was performed; the broad 8.xx–13.60 headline is not treated as support. |
| Graphics | `PS5_Vulkan` documents PS5-specific RADV/AGC/VideoOut work, a probe harness and measured hardware behavior. It explicitly leaves full CTS conformance open; RADV's `conformanceVersion` remains 0.0.0.0 in the reviewed README. | Maintainer measurements are not independently reproduced here. The source does not state system firmware coverage. See the [pinned driver report](https://github.com/mihawk-99/PS5_Vulkan/blob/f410e67a0241b3e8edcdbcd2a9b285dfc4a412ed/README.md). |
| Steam/Wine | Playden documents a PS5-native launcher/runtime, Wine, DXVK for D3D 8–11, vkd3d-proton for D3D12, and Mesa/Zink. Its README calls it alpha and says the runtime kit is tested as a matching kit. | `fw1360-dev1` is a kit directory label, not proof of installed system firmware compatibility. Playden requires a jailbroken console and root-level helpers. This project did not install or run it. See [pinned Playden README](https://github.com/leolobato/playden-ps5/blob/4805a0b9fb7cd0ea0d3077580850bf44e8bc0b6a/README.md). |
| App management and SDK | ProsperoStore is a GPL-3.0 native catalog/app manager; the public payload SDK is the low-level build input referenced by graphics and homebrew projects. | Neither establishes a firmware compatibility range. Store dependencies and payload SDK components need file-level license review before reuse. |
| Host-side translation | KytyPS5 is a GPL-2.0-only Windows/Linux translation layer with experimental macOS support and a community compatibility list. An experimental `prosper` repository also describes a user-space PS5-to-PC layer. | Host-side game translation is separate from console firmware support. `prosper` has no SPDX license declaration and is not reusable. No emulator was run. |
| App and compute examples | PS5 RetroArch and PS5LM illustrate native application and graphics/compute dependencies around PS5_Vulkan, Mesa, OpenGL and the payload SDK. | Application-level reports are maintainer evidence; they do not yield a 14.10 compatibility result. |

The matrix also normalizes selected earlier claims from PSFree, UMTX, Relapse, CSSFontFace, Byepervisor, the source-validation work and existing 14.10 repositories. It separates vulnerability-impact ranges from integrated chain support and from a homebrew/Linux test. A supported list entry, code offset, release tag, or issue impact range alone is never treated as independently reproduced execution.

## Freedom OS capability and license view

The capability table is a dependency map for planning, not a build recipe. It separates:

1. Boot and kernel access from userland packaging.
2. Linux GPU/display support from PS5-native AGC/VideoOut drivers.
3. Desktop Steam/Proton from the console-side Playden/Wine runtime.
4. Host-side PS5 title translation from running a PS5 homebrew application.

The promising reusable architecture is a documented Linux distribution and user-space software stack, but the 14.10 boot/security gate is unresolved. The native RADV work is not evidence of a drop-in `amdgpu` path: the pinned project describes PS5-specific AGC, direct memory and VideoOut interfaces. Wine, DXVK and vkd3d-proton carry separate licenses; Steam is proprietary; downstream bundles need a complete per-file notice audit. Unlicensed repositories are indexed for research only and are excluded from reuse.

## Incremental update job

GitHub API polling is implemented in `ps5knowledge update-sources` and is disabled by default in `ecosystem.json`. The default command makes no network request and writes no state. After explicit approval, set the repository variable `PS5_RESEARCH_UPDATES_ENABLED=true`; the scheduled workflow then:

- Reads configured public repository metadata and pinned default-branch commits.
- Requests commits and issues/pull requests updated since the saved timestamp, and checks recent releases; it does not clone repositories.
- Retains source URLs, IDs, observed timestamps, the checked license, and commit identity.
- Keeps repository search matches as unreviewed candidates rather than adding them automatically to trusted sources.
- Writes activity as `UNVERIFIED_SOURCE_ACTIVITY`; only a researcher can edit and reclassify a compatibility claim after source review.
- Rebuilds the ignored local SQLite database and dashboard, then opens a draft PR for the JSON update state and report.

The scheduled workflow must first be integrated into the default branch before GitHub schedule events can execute. It is currently gated off, and account-level Actions billing restrictions may prevent a run even after the gate is intentionally enabled. Local tests mock the API and never access a PS5 or the network.

## Reproduction

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -S -m unittest discover -s tests -v
python -S -m ps5knowledge build-db
python -S -m ps5knowledge stats
python -S -m ps5knowledge search '13.60 Linux Vulkan'
python -S -m ps5knowledge dashboard
python -S -m ps5knowledge update-sources  # safe no-op: disabled by default
```

The generated SQLite database and dashboard remain local/ignored. `catalog.json`, `ecosystem.json`, and any future `updates.json` are the reviewable source data. No Sony firmware, extracted binary, exploit payload or console observation is used.
