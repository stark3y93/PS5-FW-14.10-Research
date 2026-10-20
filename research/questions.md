# Ranked research questions

1. **Can 14.10 device claims be independently authenticated?** The two 14.10 repositories contain author-provided results, but console identity, firmware evidence, and capture integrity need independent review. Prefer static audit of committed records and methods; no device probing in this project.
2. **Which public disclosures actually affect firmware 14.10?** Map each candidate to an official advisory, patch chronology, reachable component, and a version-specific artifact. A matching upstream version string alone is insufficient.
3. **Can historical Sony packages be tied to an official version and hash?** The local cross-version comparison is gated on Sony-controlled provenance; candidates alone should not be labelled as firmware samples.
4. **What do the unexplained SLB2 wrapper bytes represent?** Compare independently sourced, intact wrappers across official versions and separate repeatability from interpretation. Do not infer a cryptographic role from entropy.
5. **Which upstream offline tools have reproducible correctness gaps?** Audit `ps5-pup-unpacker` input boundaries and `ZigZagBoi1` evidence parsers using synthetic fixtures, while respecting their licences and contribution guides.
6. **What evidence is needed to distinguish SDK support from general runtime compatibility?** Firmware-specific offset tables, a build success and device operation are separate claims; `PS5SDK` documents only older kernel-helper offsets.

Questions 1–3 have the highest impact on the project's compatibility conclusions. The ranking reflects missing evidence, not predicted exploit feasibility.
