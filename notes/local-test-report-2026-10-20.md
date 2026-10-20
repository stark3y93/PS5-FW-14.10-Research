# Local test report — 20 October 2026

## Scope and environment

Branch `coordination/multi-agent-2026-10-20` was created from integration commit `c2d627a`. Tests ran on Windows with Python 3 and only synthetic fixtures. No original firmware, real PS5, third-party exploit or payload was read or run. The pre-existing integration checkout and `main` were not modified.

## Reproduce

From the coordination worktree:

```powershell
$env:PYTHONPATH = 'src'
python -S -m unittest discover -s tests -v
Get-Content research\sources.json -Raw | ConvertFrom-Json | Out-Null
git diff c2d627a..HEAD --check
git ls-files artifacts derived
```

## Results

| Check | Result |
| --- | --- |
| Baseline at `c2d627a` | 49/49 synthetic tests passed |
| Integrated coordination branch | 50/50 synthetic tests passed, including rejection of an impossible prior survey plan |
| Knowledge ledger | Valid JSON; seven distinct pinned repositories and 18 classified evidence links |
| Diff whitespace | `git diff c2d627a..HEAD --check` clean |
| Tracked data directories | Only `artifacts/.gitkeep` and `derived/.gitkeep` |
| Independent review | Agent 5 accepted the survey fix, vulnerability ledger, corrected source index and upstream proposal note in `independent-review-2026-10-20.md` |

The external Relapse documentation draft has its own static allowlist and diff checks in the independent review note. The other upstream fixes are proposals without compiled regressions. GitHub Actions execution is unavailable under the existing billing restriction; local passing tests do not imply a CI result or firmware 14.10 exploit compatibility.
