# Multi-agent research plan — 20 October 2026

## Scope and decision rules

This work studies public source, documented disclosures, and synthetic offline inputs. The original 14.10 package and PS5 remain untouched. A source claim is recorded separately from a reproduced observation; neither an older firmware range nor a plausible vulnerability implies 14.10 compatibility. No third-party payload or exploit is run. No Sony package, keys, extracted content, or credentials enter Git.

Every finding should record a source URL, immutable revision or document date, the observed text or code location, an evidence class (`direct`, `author claim`, or `interpretation`), and a limitation. Proposed upstream changes require a reproducible issue, tests, licence check, and review before any publication. The coordinator selects changes by source and test evidence, not by agent agreement.

## Isolation and handoff

The pre-existing `integration/research-toolkit-2026-10-20` checkout is clean at `c2d627a` and remains untouched. New work starts from that commit in separate worktrees. Agents commit in their own branches and send the coordinator commit IDs and test output. The coordinator reviews diffs, cherry-picks only accepted commits into `coordination/multi-agent-2026-10-20`, runs independent synthetic tests, and records conflicts or rejected claims. There is no merge into `main` or existing PRs without approval.

| Role | Owner | Branch / worktree | Initial assignment | Handoff gate |
| --- | --- | --- | --- | --- |
| 1 Research Intelligence | `intelligence` | `research/intelligence-2026-10-20` / `D:\Workspace\PS5-Intel-2026-10-20` | Verify named public repositories; build source and question index | Pinned sources and evidence classes |
| 2 Firmware Analysis | `firmware` | `research/firmware-validation-2026-10-20` / `D:\Workspace\PS5-Firmware-2026-10-20` | Review parser, survey, comparison; implement small synthetic validation fix | Independent test review |
| 3 Public Vulnerability Research | `vulnerabilities` | `research/public-vulnerabilities-2026-10-20` / `D:\Workspace\PS5-Vulns-2026-10-20` | Review primary disclosures and 14.10 evidence gap | Source and applicability review |
| 4 Open-Source Engineering | `upstream` | `research/upstream-engineering-2026-10-20` / `D:\Workspace\PS5-Upstream-2026-10-20` | Four source-backed proposals and one local documentation draft | Proposal note `345fa86`; external draft `7e07020`, not published |
| 5 Testing and Verification | `verification` | `review/independent-2026-10-20` / `D:\Workspace\PS5-Verification-2026-10-20` | Independently reviewed all submissions and reran synthetic suite | Accepted after evidence-label correction; note `38ee5d2` |
| 6 Integration and Coordination | `root` | `coordination/multi-agent-2026-10-20` / `D:\Workspace\PS5-Coord-2026-10-20` | Manage branch ownership, baseline, integration, task board and final report | No conflicting edits, source-only diff |

## Task board

| ID | Owner | Task | State | Dependency |
| --- | --- | --- | --- | --- |
| RI-1 | 1 | Verify the seven named repositories and pin relevant sources | Done | None |
| RI-2 | 1 | Build a searchable evidence and question index | Done after reviewer correction | RI-1 |
| FA-1 | 2 | Audit offline tools and implement a bounded validation improvement | Done | None |
| PV-1 | 3 | Record primary disclosures and assess 14.10 evidence | Done | None |
| OS-1 | 4 | Prepare at least three evidence-backed upstream proposals | Done: four proposals, one local draft | RI-1 |
| TV-1 | 5 | Independently review integrated diffs and synthetic tests | Done: accepted, 50 tests | FA-1, RI-2, PV-1, OS-1 |
| IC-1 | 6 | Review open PR context and preserve integration checkout | Done with PR-state limitation below | None |
| IC-2 | 6 | Integrate accepted commits into coordination branch | Done | TV-1 |

## Existing pull request context

The integration manifest records PRs #4–#11 as open at its review time and explains that their useful commits were included in the current integration candidate. A read-only `git ls-remote origin 'refs/pull/*/head'` on 20 October 2026 returned heads for #4–#11. Pull refs alone do not prove current open/closed status; GitHub CLI is unavailable and the private repository's web PR page is inaccessible without authenticated API access. No existing PR was changed.

## Initial verification

The untouched integration commit `c2d627a` passed 49 synthetic unit tests locally with `PYTHONPATH=src python -S -m unittest discover -s tests -v` on 20 October 2026. `git diff --check` was clean. This tests source behavior only; it provides no 14.10 exploit or firmware compatibility evidence. GitHub Actions remains blocked by the billing restriction documented in the integration manifest.
