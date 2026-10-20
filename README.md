# PS5 system software 26.06-14.10.00 research

This workspace holds a read-only, offline investigation of Sony's public PS5 **update** package. It contains an original SLB2 metadata parser, a bounded byte-statistics experiment, tests, and an evidence-led source review. The original package is in Git-ignored `artifacts/`; generated reports belong in Git-ignored `derived/`.

## Current state

- Sony's [release notes](https://www.playstation.com/en-gb/support/hardware/ps5/system-software-info/) identify version `26.06-14.10.00`.
- The package was downloaded from the **PS5 console update file** link on Sony's [UK system software page](https://www.playstation.com/en-gb/support/hardware/ps5/system-software/). It is the `sys_...` update package, not the `rec_...` reinstallation package.
- The download is complete and its observed length, hashes, and container header are recorded in [notes/provenance.md](notes/provenance.md) and [notes/initial-findings.md](notes/initial-findings.md).
- A strict metadata-only parser and deterministic entropy sampler are in `src/ps5fwlab/`; automated tests use synthetic fixtures in `tests/`.
- No console settings, firmware, DNS, files, or services were changed. No update was installed or sent to the console.

## Reproduce locally

Requires Python 3.10 or newer. The package has no runtime dependencies.

```powershell
python -m pip install -e .
python -m unittest discover -s tests -v
Get-FileHash -LiteralPath 'artifacts\PS5UPDATE-26.06-14.10.00.PUP' -Algorithm SHA256
python -m ps5fwlab inspect 'artifacts\PS5UPDATE-26.06-14.10.00.PUP' > 'derived\slb2-metadata.json'
python -m ps5fwlab entropy 'artifacts\PS5UPDATE-26.06-14.10.00.PUP' --window 65536 --samples 256 > 'derived\inner-pup-entropy-64k-256.json'
```

The expected SHA-256 is `C17384946DF6E5C85B2D72CBEEE2057B165BF90279D9E2A86D527D0778CDAAF6`. A fresh clone must acquire the official package separately and verify its identity before running package-specific commands. `inspect` validates declared wrapper ranges without extraction. `entropy` samples only inside validated entries; its statistics cannot identify encryption or executable content.

## Research results

- [Local 14.10 artifact analysis](notes/analysis-14.10.md)
- [Comparison matrix separating facts, claims, and hypotheses](notes/comparison-matrix.md)
- [GitHub source, license, and commit review](notes/source-review.md)
- [Three ranked PC-only experiments and the reproduced result](notes/experiments.md)
- [Independent hash-verified window survey and its limits](notes/independent-survey-14.10.md)

## Scope and method

1. Preserve `artifacts/PS5UPDATE-26.06-14.10.00.PUP` as the source artifact. Recompute its SHA-256 before relying on a later analysis result.
2. Perform bounded, offline parsing of headers and file tables. Record offsets, raw bytes, parser assumptions, and validation checks alongside conclusions.
3. Keep extracted content, if any, in `derived/` with source byte ranges and hashes. Treat names and apparent file types as hypotheses until independently validated.
4. Distinguish direct observations, interpretations, and unknowns. Do not infer live console behavior from a static package.
5. If a decrypted or executable component becomes legitimately available, analyze that component as a separate artifact with its own provenance. Do not execute extracted code on the host.

## Research questions

- What are the verified outer-container layout, entry count, offsets, sizes, and padding?
- Which inner structures can be identified from public bytes without keys or a live console?
- Which findings are specific to 14.10, and which need a verified earlier update package for comparison?
- What can be corroborated by Sony's release notes and published open-source notices?

## Boundaries

This workspace does not contain an exploit, authentication bypass, decrypted PS5 system image, or a claim of complete firmware coverage. The initial live-network observations from the prior check establish local reachability only; they do not identify firmware internals.

The next technical obstacle is verified access to the inner PUP's protected contents or a documented, independently validated public header layout beyond its observed magic. No code here connects to a PS5.
