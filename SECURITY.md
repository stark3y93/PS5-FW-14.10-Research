# Security policy and responsible research

## Supported scope

This repository is an **offline, read-only research toolkit**. It is not a PS5 jailbreak, exploit loader, firmware mirror, or key repository.

## Reporting a security issue

Please **do not publish credentials, private IP addresses, personal identifiers, firmware binaries, exploit details affecting unpatched devices, or private crash traces in a public issue**.

If GitHub's **Report a vulnerability** / private vulnerability reporting feature is available for this repository, use that. Otherwise contact the repository owner privately through a trusted channel; do not assume public issues are confidential.

For suspected vulnerabilities in Sony or upstream components, follow the affected vendor's coordinated vulnerability disclosure process. Include minimal reproducible evidence, affected versions and source references where lawfully available.

## Data handling

- Keep original Sony firmware files, extracted proprietary binaries, secrets, dumps, and network captures out of Git history.
- Keep generated output in ignored `derived/` and firmware in ignored `artifacts/`.
- Redact console/PC addresses, account names, access tokens, device identifiers, request headers, and personal paths from shared logs.
- Never commit `.env` or private keys. Use placeholder values in examples.
- The `.gitignore` helps prevent **accidental new additions** but does **not** protect files already tracked or erase previous commits.
- If a secret was exposed, revoke/rotate it first; removing a file from the current branch does not remove it from Git history.
- Review the actual staged diff (`git diff --cached`) before publishing.

## Security claims

Use evidence labels: **upstream-confirmed**, **observed on device**, **unverified on PS5 14.10**, **contradicted**, or **not tested**. Do not equate debug settings, malformed input acceptance, arithmetic overflow, a missing beacon, or a browser crash with kernel code execution or a jailbreak.

No live exploit attempts or console changes are required to contribute offline analysis.
