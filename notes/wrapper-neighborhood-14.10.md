# SLB2 wrapper neighborhood map: official 14.10 update

## Reproduction and scope

Local source: `artifacts/PS5UPDATE-26.06-14.10.00.PUP` (Git ignored). Before and after the experiment, full-file SHA-256 was checked against `C17384946DF6E5C85B2D72CBEEE2057B165BF90279D9E2A86D527D0778CDAAF6`. The command also hashes before and after sampling. It reads the first 512 bytes for validated SLB2 metadata and at most two 512-byte samples per region. It creates no extracted file. The full 256-bin numerical histograms are written only to ignored `derived/wrapper-neighborhood-14.10.json`.

```powershell
$env:PYTHONPATH=(Join-Path (Get-Location) 'src')
python -m unittest discover -s tests -v
python -m ps5fwlab map 'artifacts\PS5UPDATE-26.06-14.10.00.PUP' --sha256 C17384946DF6E5C85B2D72CBEEE2057B165BF90279D9E2A86D527D0778CDAAF6 > 'derived\wrapper-neighborhood-14.10.json'
Get-FileHash -LiteralPath 'artifacts\PS5UPDATE-26.06-14.10.00.PUP' -Algorithm SHA256
```

## Direct observations

Offsets below are zero-based half-open intervals. Entropy is empirical Shannon entropy of the **bounded sample**, in bits per byte; it is not an estimate of cryptographic strength.

| Region | Interval | Length | Zero bytes measured | Distinct byte values | Sample entropy |
| --- | ---: | ---: | ---: | ---: | ---: |
| Declared header | `[0, 32)` | 32 | 22 | 10 | 1.8716 |
| One entry record | `[32, 80)` | 48 | 29 | 16 | 2.4416 |
| Unused first header block | `[80, 512)` | 432 | 432 | 1 | 0 |
| Pre-entry block | `[512, 1024)` | 512 | 448 | 55 | 1.2530 |
| Declared entry | `[1024, 1261407805)` | 1,261,406,781 | first/last 512: 4 / 1 | 221 / 223 | 7.5835 / 7.6062 |
| Final gap | `[1261407805, 1261408256)` | 451 | 451 | 1 | 0 |

The wrapper has one entry. Its start is 512-byte aligned. Its end is 61 bytes into a 512-byte block, leaving exactly 451 bytes to the file boundary. The declared length and the whole file length agree with the validated SLB2 block count. The pre-entry block's 64 nonzero bytes occupy **two 32-byte runs**, at `[512, 544)` and `[992, 1024)`; the intervening 448 bytes are zero. This refines the previously recorded observation that the block contains 64 nonzero bytes. No byte sequences from the package are included here.

The samples at the entry's first and last 512 bytes are diverse, but the unmeasured interior is large. High sample entropy cannot distinguish encryption from compression or other encoding. The 451-byte zero gap is consistent with block padding, but this single file cannot establish a format rule.

## Source comparison and hypotheses

- [Hykem's PS4 SLB2 unpacker, mirrored by nikosradio at `2aabe4da09ba14c41f3a0d8516aa756742ef4688`](https://github.com/nikosradio/ps4tools/blob/2aabe4da09ba14c41f3a0d8516aa756742ef4688/pupunpack.c) documents a 0x20-byte header, 0x30-byte entries, 512-byte blocks, and block-based offsets. Its extraction loop assumes payloads start at 0x200 and advances by rounded sizes. Our PS5 14.10 entry record instead declares block offset 2 (0x400), leaving the measured pre-entry block. This is a **source-layout difference**, not proof that the PS4 code handles PS5 or that the second block has a particular function. We do not copy or run the GPL-2.0 code.
- [zecoxao's PS5 PUP unpacker README at `005cccc908142c35ab7280e7f9eef8d5203c21e0`](https://github.com/zecoxao/ps5-pup-unpacker/blob/005cccc908142c35ab7280e7f9eef8d5203c21e0/README.md) says its input has already been decrypted. Its [PUP.cpp](https://github.com/zecoxao/ps5-pup-unpacker/blob/005cccc908142c35ab7280e7f9eef8d5203c21e0/PUP.cpp) does not provide evidence that this original inner entry can be parsed as a decrypted file. We make no such claim.
- **Hypothesis, untested:** the two 32-byte runs could be integrity-related fields. Their size and placement alone do not identify them as digests, signatures, keys, or any other specific structure. A test against independently verified official update packages of other versions is needed.
- **Novelty assessment:** the two-run placement is a new, reproducible *local observation* relative to this project's previous notes. We found no basis to call it a previously undocumented SLB2 format feature or a 14.10-specific anomaly. One package and historical PS4 code are insufficient for that claim.

## Next experiment

Highest potential for an original contribution: repeat this exact hash-verified map on at least two other official PS5 update packages with documented provenance, then compare the second-block occupancy, run placement, field stability, entry offsets, and padding. Pre-register the measured offsets and avoid comparing raw copyrighted bytes. A stable pattern across versions could support a structural hypothesis; a changing pattern could guide later public-format research. The inner entry remains inaccessible as a validated decrypted structure, and nothing here establishes console behavior.
