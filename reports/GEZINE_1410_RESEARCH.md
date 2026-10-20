# Gezine and PS5 14.10: public evidence review

**As of 20 October 2026.** This report distinguishes a public demonstration from a reproducible exploit. It does not assume that this repository's browser candidates are related to Gezine's work.

The named repository contains an offline firmware-wrapper toolkit, not browser probes. Browser claims discussed in the companion matrix come from the separate desktop checkout identified there.

## What can be verified

1. Gezine's [original X post](https://x.com/gezine_dev/status/2112279793911968218), dated 19 October, says “Hello 14.10”. Multiple reports describe its video as showing system version `26.06-14.10.00` and the `★ Debug Settings` menu on a PS5. X did not expose the video to this audit's web reader, so frame-level authenticity and retail hardware status were **not independently established here**. The public demonstration strongly suggests privileged behavior but does not show a kernel memory read/write primitive, a debug trace, or a reproducible chain. [Contemporary account](https://www.biteyourconsole.net/2026/10/20/gezine-mostra-i-debug-settings-sul-firmware-14-10-della-playstation-5-ecco-cosa-sappiamo-davvero-sul-jailbreak/).
2. Gezine's follow-up statement, reproduced by [a contemporary account](https://gamegaz.com/2026102046313/) and [a social post mirror](https://www.sotwe.com/PS5_JB), says the kernel exploit used on 13.xx was patched in 14.00, disclosure would be requested later, and “It's not relapse.” This describes the **older 13.xx method**; it is not a disclosure of the 14.10 mechanism.
3. A later statement attributed to Gezine says the old executable-dumping route does not seem to work on 14.xx and speculates that a hypervisor exploit may be needed. This is the researcher's assessment, not a demonstrated universal requirement. [Contemporaneous mirror](https://www.sotwe.com/PS5_JB).
4. [Gezine's public GitHub profile](https://github.com/Gezine) and [Luac0re repository](https://github.com/Gezine/Luac0re) show earlier userland work. The Luac0re README explicitly distinguishes native userland execution from a kernel exploit and limits its included kernel payload to older firmware. This audit found no public 14.10 exploit source, build instructions, or reproducible release under Gezine's public repositories. This is a time-bounded search result, not proof that no private code exists.

## Interpretation

| Question | Evidence-based answer |
|---|---|
| Has kernel execution on 14.10 been demonstrated? | Gezine appears to have demonstrated Debug Settings on 14.10 and referred to a kernel exploit in follow-up discussion. The available public artifact does **not independently prove kernel code execution or kernel R/W**. Describing it as a claimed private kernel exploit is fair; describing it as an independently verified full jailbreak is not. |
| Is source publicly obtainable? | No 14.10 source or reproducible procedure was found in the checked public repositories and posts as of this date. |
| Vulnerability class/component? | Undisclosed. A kernel privilege-escalation path is a plausible inference from the menu and the researcher's language. No specific syscall, race, UAF, CVE, or browser entry point has been disclosed for this 14.10 result. |
| Prerequisite/firmware range? | The demonstration refers to 14.10. The earlier 13.xx kernel method was said to be patched in 14.00. Support on other 14.xx versions, required userland entry, console model, and hypervisor status are unverified. |

Do not join this demonstration to CSSFontFace, MetadataTable, Relapse, or a FreeBSD CVE without new primary evidence. Showing a settings menu does not establish protected game executable access or hypervisor compromise.
