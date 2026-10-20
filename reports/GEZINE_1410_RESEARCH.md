# Gezine and PS5 14.10: public evidence review

**As of 20 October 2026.** This report distinguishes a public demonstration from a reproducible exploit. It does not assume that this repository's browser candidates are related to Gezine's work.

The named repository contains an offline firmware-wrapper toolkit, not browser probes. Browser claims discussed in the companion matrix come from the separate desktop checkout identified there.

## What can be verified

1. Gezine's [original X post](https://x.com/gezine_dev/status/2112279793911968218), dated 19 October, says “Hello 14.10”. A contemporary report describes the video showing system version `26.06-14.10.00` and the `★ Debug Settings` menu. X did not expose the video itself to this audit's web reader, so frame-level authenticity and retail hardware status were **not independently established here**. This is evidence of a meaningful device result, not a reproducible kernel read/write chain. [Contemporary account](https://gamegaz.com/2026102046313/).
2. Gezine's follow-up statement, reproduced by [a contemporary account](https://gamegaz.com/2026102046313/) and [a social post mirror](https://www.sotwe.com/PS5_JB), says the kernel exploit used on 13.xx was patched in 14.00, disclosure would be requested later, and “It's not relapse.” This describes the **older 13.xx method**; it is not a disclosure of the 14.10 mechanism.
3. A later statement attributed to Gezine says the old executable-dumping route does not seem to work on 14.xx and speculates that a hypervisor exploit may be needed. This is the researcher's assessment, not a demonstrated universal requirement. [Contemporaneous mirror](https://www.sotwe.com/PS5_JB).
4. Gezine's [public GitHub profile](https://github.com/Gezine) and [Luac0re repository](https://github.com/Gezine/Luac0re) expose earlier userland work, not the 14.10 method. A separate community [14.10 research repository](https://github.com/ZigZagBoi1/PS5-14.10-Research) reports native userland thread-ROP execution and a controlled user-memory write (README and probe index). However, its linked raw [80k capture](https://github.com/ZigZagBoi1/PS5-14.10-Research/blob/9c89819cf74002b616108bd674b398ae919b40b6/results/phase17_new_vectors/80k_rop_chain_20261019_223328.txt) contains only the process ID, a reported module address, and “Scanning for syscall;ret gadget...”; it does not record the claimed write result. Treat the broader project claim as **maintainer-reported, not independently confirmed by that linked capture**. The project itself says kernel read/write and a validated 14.10 kernel vulnerability remain unestablished. This is not Gezine's exploit source.

## Interpretation

| Question | Evidence-based answer |
|---|---|
| Has kernel execution on 14.10 been demonstrated? | Gezine showed Debug Settings and referred to a kernel exploit, but available material does not independently establish the method or kernel R/W. Another public project reports userland thread-ROP, but the linked raw `80k` output is incomplete and does not show the reported write. No independently reproducible 14.10 kernel execution is established by this audit. |
| Is source publicly obtainable? | No source or reproducible procedure for Gezine's 14.10 exploit was found. The separate research repository publishes its own userland probes and evidence references; they do not disclose Gezine's method. |
| Vulnerability class/component? | Gezine's 14.10 mechanism remains undisclosed. The public research project describes userland thread/context control, ROP, and syscall experiments; the linked raw `80k` capture stops before its stated outcome, and the project's KASLR avenues are reported as negative or incomplete. These are not evidence for Gezine's exploit mechanism. |
| Prerequisite/firmware range? | The demonstration refers to 14.10. The earlier 13.xx kernel method was said to be patched in 14.00. Support on other 14.xx versions, required userland entry, console model, and hypervisor status are unverified. |

Do not join Gezine's result to CSSFontFace, MetadataTable, Relapse, or a FreeBSD CVE without new primary evidence. Debug Settings does not establish protected game executable access or hypervisor compromise. The separate project's userland progress is a reported result whose linked raw capture is incomplete; its own documentation says the kernel vulnerability, kernel R/W, and complete chain gates remain open.
