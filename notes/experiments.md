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

## Three next PC-only experiments (ranked)

These are proposed protocols, not performed tests or exploit attempts. The
ratings are relative to this lab: high feasibility means the input is already
available; high safety means no console contact, extraction, or execution.

| Rank | Experiment and falsifiable question | Scientific value | Feasibility | Safety |
|---|---|---|---|---|
| 1 | **Independent, preregistered window survey.** Derive a pseudorandom seed from the verified PUP SHA-256, choose 256 nonoverlapping 64 KiB windows without using the earlier offsets, and ask whether any entropy is below 7.9 bits/byte. Report the sampling frame and a binomial bound for the fraction of low-entropy windows if none are found. | High: tests whether even spacing missed islands. It still cannot classify an encoding. | High: the verified local package and sampler exist. | High: bounded reads only. |
| 2 | **Wrapper neighborhood map.** Count nonzero bytes and byte frequencies in fixed 512-byte blocks around the declared entry boundary; ask whether the 64 nonzero pre-entry bytes cluster in a repeated structure across those blocks. Publish counts and offsets, not raw firmware bytes. | Medium: narrows where a later documented format probe should focus. | High: one local package is enough. | High: bounded reads only. |
| 3 | **Cross-version wrapper control.** Independently obtain and hash an official earlier `sys` update, then compare only SLB2 field values, boundary positions, and the same predeclared window statistics. Ask which outer structures are stable across releases. | High: a control package helps separate version changes from stable layout. | Medium: needs another authentic official package and storage. | High: offline reads, with both proprietary packages excluded from Git. |

**Best next experiment:** rank 1. Pre-registering the seed, threshold and
window count before reading avoids selecting offsets after seeing results. A
zero count would constrain the prevalence of low-entropy *windows under that
sampling design*, not prove the entire entry is homogeneous or encrypted.
