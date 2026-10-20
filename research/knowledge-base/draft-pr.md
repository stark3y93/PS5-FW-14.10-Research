# Draft pull request

**Title:** Add source-linked SQLite PS5 research knowledge base and dashboard

**Base:** `main`  
**Head:** `research/max-intelligence-2026-10-20`  
**Issue:** #2 (research tracking)

## Summary

- Consolidate the existing PR #13 and source-review evidence into a structured, reviewable JSON catalog with pinned repository commits, licenses, source provenance, claim classes, evidence links, firmware/component/CVE relationships, open questions, and contradictions.
- Add a standard-library SQLite builder with normalized relationships and FTS5 search, a CLI that full-text searches all entity types, and a static local dashboard.
- Add synthetic tests for catalog referential integrity, database generation, safe full-text search, and dashboard rendering.
- Correct the evidence ledger: public WebKitGTK/WPE records exist for CVE-2026-43705 and -43715, but mapping them to reported PS5 TransformStream/CSSFontFace issues and Sony applicability remains unresolved. CVE-2026-64784 is a WebKitGTK OOB record; its PS5 MetadataTable mapping remains unresolved. FreeBSD jail advisories for CVE-2025-15547 and -15576 establish FreeBSD-only scope and fixes; Sony kernel correspondence is unknown.

## Evidence and verification

- Local command: `python -S -m unittest discover -s tests -q`
- All tests use synthetic/local research metadata; they do not read firmware, contact hardware, run third-party exploit code, or require credentials.
- The generated SQLite database and HTML dashboard are ignored, reproducible local outputs; the JSON catalog is the reviewable source of truth.
- GitHub Actions may remain blocked by the repository owner’s known account-level billing restriction; this is not presented as a workflow failure.

## Safety and limitations

- No console was accessed, no exploit or payload executed, and no Sony package/decrypted material included.
- Third-party firmware compatibility statements remain attributed claims unless primary evidence supports the bounded statement.
- No vulnerability claim is independently reproduced on a PS5; exact 14.10 component/source build mapping remains unresolved.
- Do not merge automatically.
