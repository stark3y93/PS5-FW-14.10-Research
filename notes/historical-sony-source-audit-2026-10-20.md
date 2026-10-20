# Historical Sony update metadata audit: 14.00 and 13.60

## Decision

**No historical package was admitted or downloaded.** Sony currently serves two candidate objects at its own update host, but the version-to-URL and SHA-256 assertions were found only in third-party copies of historical update lists. A live Sony HTTP HEAD response proves that an object at a specific Sony-controlled URL is available and reports its length; it does not attest the object's historical version or prove that the path's 64-character string equals the file's computed SHA-256. Sony's [current download page](https://www.playstation.com/en-gb/support/hardware/ps5/system-software/) links 14.10, while its [release notes](https://www.playstation.com/en-gb/support/hardware/ps5/system-software-info/) confirm that 14.00 and 13.60 existed but do not link their package files.

## Candidate evidence ledger

| Candidate version | Sony-hosted candidate URL checked with HTTPS HEAD | Size: archived claim / Sony HEAD | SHA-256 string in URL (not independently verified) | Version-to-URL source | Confidence and disposition |
| --- | --- | ---: | --- | --- | --- |
| `26.06-14.00.00` | [Sony CDN object](https://pc.ps5.update.playstation.net/update/ps5/official/tJMRE80IbXnE9YuG0jzTXgKEjIMoabr6/image/2026_0909/sys_1eb4b18451e0f064fc23b5bd4c95cae7f6489f9ad1148b5dfb0d66452a108ebc/PS5UPDATE.PUP) | `1,260,600,832` / `1,260,600,832` bytes | `1eb4b18451e0f064fc23b5bd4c95cae7f6489f9ad1148b5dfb0d66452a108ebc` | [Third-party archived XML at commit `83b0b510580bdbf3a2b77c05ccc7566e887be60d`](https://github.com/MewX/ps5-official-firmware-list/blob/83b0b510580bdbf3a2b77c05ccc7566e887be60d/updatelists/updatelist.2026_0909.14.00.00.xml) | **High** that Sony serves the URL and reports this size; **unverified** Sony attestation of version and full-file SHA-256. Excluded. |
| `26.05-13.60.00` | [Sony CDN object](https://pc.ps5.update.playstation.net/update/ps5/official/tJMRE80IbXnE9YuG0jzTXgKEjIMoabr6/image/2026_0717/sys_767a94eac034d33907a6ff57af05bc30ce057258ad1cf4b5ffb75d5e21112561/PS5UPDATE.PUP) | `1,247,471,104` / `1,247,471,104` bytes | `767a94eac034d33907a6ff57af05bc30ce057258ad1cf4b5ffb75d5e21112561` | [Third-party archived XML at commit `7f4ed6a8d7395d22e260563a189756ec6308ca46`](https://github.com/MewX/ps5-official-firmware-list/blob/7f4ed6a8d7395d22e260563a189756ec6308ca46/updatelists/updatelist.2026_0717.13.60.00.xml) | **High** that Sony serves the URL and reports this size; **unverified** Sony attestation of version and full-file SHA-256. Excluded. |

The third-party XML copies contain `system_pup` labels, `upd_version`, image lengths, and `http://dus01...` image URLs. For the HEAD checks, only the host and scheme were changed to Sony's `https://pc.ps5.update.playstation.net` endpoint; the image path, build-date segment, and `sys_...` segment were preserved. The archived XML is evidence of a community record **about** a purported Sony response, not an authenticated response **from** Sony today. Sony's current live [US update list](http://fus01.ps5.update.playstation.net/update/ps5/official/tJMRE80IbXnE9YuG0jzTXgKEjIMoabr6/list/us/updatelist.xml) has one `system_pup` entry for 14.10. Its `force_update` element mentions 13.60, but that is a requirement field, not a 13.60 image URL. The live Japan list also pointed to 14.10 in the earlier check. No Sony-published historical manifest endpoint or direct historical package link was found in the checked official pages.

## Direct Sony response observations

At approximately 11:27 UTC on 20 October 2026, both Sony HTTPS HEAD requests returned `200 OK`, `Accept-Ranges: bytes`, and the Content-Length values above. The 14.00 candidate response had `Last-Modified: Tue, 15 Sep 2026 00:44:44 GMT` and ETag prefix `6e100a2f04a0e4c7b0418c72b4f7e1a9`. The 13.60 candidate had `Last-Modified: Thu, 23 Jul 2026 01:16:20 GMT` and ETag prefix `06a74efce009503170b7add7fecfeb36`. Those dates and ETags are server metadata and offer consistency checks, but they do not establish the PS5 firmware version or authenticate the claimed SHA-256. No GET of either large object was made.

## Protocol and source distinction

The observed Sony update-list XML uses a `system_pup` element with `label`, `upd_version`, `update_data`, and an `image size` and URL. The live 14.10 list corroborates this syntax. A [community protocol description](https://www.psdevwiki.com/ps5/Updatelist.xml) explains the list path, but is not Sony documentation; no published Sony protocol specification was located. The current Sony support page is authoritative for its live linked package. An archived XML hosted on GitHub is a lead for locating a Sony object and cannot by itself transfer Sony's authority to the claimed version and digest.

## PR and local verification

- PR [#7](https://github.com/stark3y93/PS5-FW-14.10-Research/pull/7) is based on `main`; [#8](https://github.com/stark3y93/PS5-FW-14.10-Research/pull/8) is stacked on #7; [#9](https://github.com/stark3y93/PS5-FW-14.10-Research/pull/9) is stacked on #8. All three were open, mergeable, and reported a clean merge state during this audit. They should be reviewed in that order; no branch was merged.
- The 36-test suite passed locally with `PYTHONPATH=src python -S -m unittest discover -s tests -v`. PR #7's SHA-seeded survey is reproducible but does not give a formal random-sampling guarantee; PR #8's on-disk preservation test is strengthened in #9. The comparator in #9 deliberately treats sample IDs as unverified labels. No new source or security defect was found in this review.
- The existing 14.10 package's SHA-256 remained `C17384946DF6E5C85B2D72CBEEE2057B165BF90279D9E2A86D527D0778CDAAF6`. Git tracks only `.gitkeep` in `artifacts/` and `derived/`.

## Research question supported by this evidence

Can a Sony-controlled, version-bound historical update list (or another Sony-authenticated version record) be obtained for either candidate object? Until then, downloading those large packages would not resolve the provenance gap, and the two 32-byte runs observed in 14.10 cannot be tested as a **verified cross-version** pattern. Acquisition stops here rather than repeating the same source searches.
