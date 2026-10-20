# Initial static findings

## Direct observations

- Offset `0x0000`: ASCII `SLB2` (`53 4C 42 32`).
- Little-endian 32-bit value at `0x0004`: `3`.
- Little-endian 32-bit value at `0x000C`: `1`.
- Little-endian 32-bit value at `0x0010`: `2,463,688`; multiplied by 512, this equals the exact file length.
- The sole observed table entry begins at `0x0020`. Its first 32-bit value is `2`, corresponding to byte offset `0x0400` when interpreted as 512-byte blocks.
- The next 32-bit value is `1,261,406,781`, which fits within the source file when measured from `0x0400`.
- The entry name bytes at `0x0030` read `PS5UPDATE1.PUP` followed by NUL padding.
- The first 16 bytes at `0x0400` are `54 14 F5 EE 10 01 01 32 04 00 00 00 B0 05 E0 0D`.

## Interpretation and limits

The outer header and table are consistent with an `SLB2` package containing one named inner PUP. The field interpretations above are checked against this file's length and bounds; the exact semantics of the value `3`, inner header, cryptographic protection, and payload contents have **not** been established here. The file has not been executed, installed, or sent to a PS5.

Prior network checks found that `192.168.4.30` replied to ping and accepted TCP connections on port `9295`. That observation does not identify this package's components or confirm that the console runs 14.10.
