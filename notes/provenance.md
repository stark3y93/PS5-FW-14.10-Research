# Artifact provenance

| Field | Recorded value |
|---|---|
| Artifact | `artifacts/PS5UPDATE-26.06-14.10.00.PUP` |
| Package type | PS5 console **update** file (`sys` path) |
| Sony source page | https://www.playstation.com/en-gb/support/hardware/ps5/system-software/ |
| Source URL | https://pc.ps5.update.playstation.net/update/ps5/official/tJMRE80IbXnE9YuG0jzTXgKEjIMoabr6/image/2026_0928/sys_c17384946df6e5c85b2d72cbeee2057b165bf90279d9e2a86d527d0778cdaaf6/PS5UPDATE.PUP |
| Downloaded | 2026-10-20 (Europe/London) |
| HTTP status | 200 |
| Server Content-Length | 1,261,408,256 bytes |
| Server Last-Modified | Wed, 14 Oct 2026 06:46:50 GMT |
| Server ETag | `f7853a0fa97a9a7828ac548798012782:1791960437.590458` |
| Observed file length | 1,261,408,256 bytes |
| SHA-256 | `C17384946DF6E5C85B2D72CBEEE2057B165BF90279D9E2A86D527D0778CDAAF6` |
| MD5 | `F7853A0FA97A9A7828AC548798012782` |

The SHA-256 equals the 64-hex-character digest in the Sony URL path. The MD5 equals the first field of the server ETag. These are useful consistency checks, not a substitute for a cryptographic signature validation.

To verify the local file again in PowerShell:

```powershell
Get-FileHash -LiteralPath 'D:\Workspace\PS5-FW-14.10-Research\artifacts\PS5UPDATE-26.06-14.10.00.PUP' -Algorithm SHA256
```
