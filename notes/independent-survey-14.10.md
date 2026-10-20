# Independent 14.10 byte-window survey

## Protocol fixed before the local run

Input is the existing, ignored official update PUP, expected full-file SHA-256
`C17384946DF6E5C85B2D72CBEEE2057B165BF90279D9E2A86D527D0778CDAAF6`.
The current command verifies that hash before and after reading sample windows
and validates the SLB2 interval. For each entry, the sampling frame is complete 65,536-byte
windows aligned to its start. Windows touching any of the earlier 256 evenly
spaced windows are removed from the frame. A Python `random.Random` instance
seeded by the integer SHA-256 digest selects 256 distinct remaining slots;
the selected offsets are sorted for reading. The predeclared comparison is the
count with Shannon entropy **below 7.9 bits per byte**. No offset is chosen in
response to the bytes observed at that offset.

```powershell
$env:PYTHONPATH = 'src'
python -S -m unittest discover -s tests -v
python -S -m ps5fwlab survey 'artifacts\PS5UPDATE-26.06-14.10.00.PUP' --sha256 C17384946DF6E5C85B2D72CBEEE2057B165BF90279D9E2A86D527D0778CDAAF6 --window 65536 --samples 256 > 'derived\independent-survey-14.10.json'
```

The output is numerical metadata only and stays ignored in `derived/`; no raw
Sony bytes are copied into Git. The `uniform_slot_model_upper_fraction_95pct`
field, when there are zero below-threshold windows, is `1 - 0.05^(1/n)`.
It is a **model-based benchmark** for uniformly sampled slots, not a formal
confidence guarantee for this fixed, content-derived seed. It applies only to
eligible aligned windows, not every byte or the excluded earlier windows.
The current planner rejects frames above one million aligned slots before
materializing candidate indices. This limit does not affect this 14.10 run.
High entropy remains compatible with encryption, compression, and other data.

## Observed result (20 October 2026)

The verified inner entry begins at byte `1,024` and has length
`1,261,406,781`. It contains `19,247` complete aligned 64 KiB slots. The
prior even-window exclusions removed `510`, leaving `18,737` eligible slots.
The SHA-seeded selection produced `256` distinct windows (16,777,216 bytes),
none overlapping an earlier sampled window. The first selected offset was
`2,425,856` and the last was `1,257,112,576`.

| Measure | Result |
|---|---:|
| Below 7.9 bits/byte | 0 of 256 |
| Minimum entropy | 7.9964347009 bits/byte |
| Mean entropy | 7.9971942578 bits/byte |
| Maximum entropy | 7.9979777111 bits/byte |
| Mean zero-byte fraction | 0.0039237738 |
| Mean printable-ASCII fraction | 0.3712883592 |
| Uniform-slot model 95% upper benchmark after zero hits | 0.0116338762 |

The complete numerical JSON is the ignored local file
`derived/independent-survey-14.10.json`. The 1.16% benchmark is conditional
on treating the selected eligible slots as if sampled uniformly and randomly;
this fixed SHA-derived seed does not provide a formal probability guarantee.
The survey looked at about 1.33% of the inner entry and cannot classify the
remaining bytes or distinguish compression from encryption. No inner table or
executable content was decoded, and no PS5 was contacted.

### Local test evidence

Before this change, the `main` branch's firmware-free suite passed 16/16.
With the survey code and synthetic fixtures, `PYTHONPATH=src python -S -m
unittest discover -s tests -v` passed 23/23 on this PC. The survey command
verified the full-file SHA-256 before selecting windows. Its own output is
excluded by `.gitignore`.

Offset selection uses Python 3.12's `random.Random.sample` implementation;
the saved numerical JSON includes every chosen offset so later comparisons
can detect any change in that implementation on another Python version.
