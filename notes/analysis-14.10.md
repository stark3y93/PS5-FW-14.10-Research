# Static analysis of the 14.10 update package

## Identity

The original local file is `artifacts/PS5UPDATE-26.06-14.10.00.PUP`, 1,261,408,256 bytes, SHA-256 `C17384946DF6E5C85B2D72CBEEE2057B165BF90279D9E2A86D527D0778CDAAF6`. Its Sony download URL and server metadata are in [provenance.md](provenance.md). Sony's [release notes](https://www.playstation.com/en-gb/support/hardware/ps5/system-software-info/) name `26.06-14.10.00`; the version is not inferred from the file header.

## Bounded outer-wrapper observations

| Byte range / field | Direct observation | Validation |
|---|---|---|
| `0x0000` | ASCII `SLB2` | Exact four-byte magic. |
| `0x0004` | Little-endian value `3` | Retained as a version-like raw field; semantics not proven. |
| `0x000C` | Entry count `1` | One 0x30-byte table entry fits in the first 512-byte block. |
| `0x0010` | Block count `2,463,688` | × 512 equals the exact 1,261,408,256-byte file length. |
| `0x0020` table entry | Block offset `2`, size `1,261,406,781`, name `PS5UPDATE1.PUP` | Start `0x0400` (1024); end `1,261,407,805`, within the file. |
| `0x0200–0x03FF` | 512-byte pre-entry region, 64 nonzero bytes | This region is not interpreted as empty padding or a verified signature. |
| After inner entry | 451 bytes, all zero | End padding to the next 512-byte boundary. |

The table layout agrees with historical [PS4 `SLB2` source](https://github.com/nikosradio/ps4tools/blob/2aabe4da09ba14c41f3a0d8516aa756742ef4688/pupunpack.c), but the local field values and bounds were measured independently. The parser uses each entry's declared offset and rejects malformed or overlapping ranges; it does not copy the historical extraction behavior.

## Inner PUP boundary

At byte `0x0400` of the original, the first 16 bytes are:

`54 14 F5 EE 10 01 01 32 04 00 00 00 B0 05 E0 0D`

The first four bytes match the PS5 PUP magic checked by [zecoxao's PUP parser](https://github.com/zecoxao/ps5-pup-unpacker/blob/005cccc908142c35ab7280e7f9eef8d5203c21e0/PUP.cpp). Its [README](https://github.com/zecoxao/ps5-pup-unpacker/blob/005cccc908142c35ab7280e7f9eef8d5203c21e0/README.md) requires a previously decrypted input. This lab does **not** decode its entry table, call the unpacker, label its payload encrypted, or treat any bytes as runnable code.

The [byte-statistics experiment](experiments.md) sampled 256 windows inside this entry. Every sampled window had entropy above 7.996 bits per byte. This is compatible with several encodings (including compression and encryption) and covers only about 1.33% of the entry. No conclusion about the unsampled 98.67% is made.

## Limits

The package does not establish the firmware version installed on the user's console. Static wrapper bytes cannot establish the state of WebKit, kernel vulnerabilities, security mitigations, or a working exploit on 14.10. No live console interaction occurred during this continuation.
