# Three safe, PC-only research experiments

These are original **lab designs** for the locally acquired official package, not claims of novelty in firmware research. They avoid console traffic, payloads, settings changes, and execution of extracted bytes.

| Rank | Experiment | Why useful | Input and limit | Status |
|---|---|---|---|---|
| 1 | **Stratified inner-entry byte profile.** Validate SLB2 bounds, then sample fixed-size windows at deterministic offsets and compute Shannon entropy, zero-byte fraction, and printable-ASCII fraction. | Quickly finds large low-entropy islands worth later format-specific study and reveals whether the sampled distribution is homogeneous. | Official local PUP only. Sampling cannot classify encryption versus compression and misses unsampled islands. | Implemented in `src/ps5fwlab/entropy.py`; synthetic tests and the CLI integration test pass. |
| 2 | **Wrapper boundary and pre-entry region audit.** Compare raw bytes immediately before and after the declared inner entry, including nonzero positions, against independently parsed table bounds. | Tests whether supposed padding holds unmodeled metadata or signatures; no payload interpretation needed. | Current package is sufficient, but semantics of the 64 nonzero pre-entry bytes remain unknown. | Initial bounded observation recorded in [analysis-14.10.md](analysis-14.10.md); not automated as a separate command. |
| 3 | **Same-type cross-version structural diff.** Acquire an independently verified official earlier `sys` PUP, compare only wrapper fields, declared entry intervals, and deterministic byte profiles. | Distinguishes format changes from 14.10-specific content changes without accessing the console. | Requires a second authentic official package; no earlier package was supplied or downloaded. Equal entropy would not imply equal contents. | Proposed only. |

## Reproduce experiment 1

From the repository root after `python -m pip install -e .` and after verifying the original SHA-256:

```powershell
python -m unittest discover -s tests -v
python -m ps5fwlab inspect 'artifacts\PS5UPDATE-26.06-14.10.00.PUP' > 'derived\slb2-metadata.json'
python -m ps5fwlab entropy 'artifacts\PS5UPDATE-26.06-14.10.00.PUP' --window 65536 --samples 256 > 'derived\inner-pup-entropy-64k-256.json'
```

`tests/test_slb2.py` rejects invalid magic, truncated headers, declared-size mismatch, excessive entries, header overlap, out-of-file entries, overlapping entries, unsafe names, and zero-length entries. `tests/test_entropy.py` checks known entropy values, selected-range boundaries, and that input bytes remain unchanged. `tests/test_cli.py` checks both commands on a synthetic package.

## Measured result on 26.06-14.10.00

The run sampled 256 distinct 65,536-byte windows, totaling 16,777,216 bytes (about 1.33% of the `PS5UPDATE1.PUP` entry). Observed entropy ranged from **7.996277** to **7.997969** bits per byte, with a mean of **7.997182**. No sampled window was below 7.9 bits per byte. The full local JSON is `derived/inner-pup-entropy-64k-256.json` and is ignored by Git.

**Interpretation:** the sampled bytes are high entropy. This result does not show whether the inner PUP is encrypted, compressed, mixed, or usable by a given parser. The next useful offline input would be a documented header specification or a separately obtained, legitimately decrypted sample with its own provenance; this lab has neither.
