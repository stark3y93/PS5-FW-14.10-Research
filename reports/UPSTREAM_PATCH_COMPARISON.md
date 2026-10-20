# Upstream patch comparison and candidate status

Audit date: 20 October 2026. Source comparisons below use published upstream patches/advisories. No Sony 14.10 WebKit or kernel source tree, symbolized binary, or authorized comparison build was available. Therefore upstream patch state on PS5 14.10 remains unknown.

## CSSFontFace lifetime issue

WebKit commit [`5aedb82710ba578f`](https://github.com/WebKit/WebKit/commit/5aedb82710ba578f), titled “Use-after-free in CSSFontFace::setStatus via CSSFontFace::load”, changes `Source/WebCore/css/CSSFontFace.cpp` around lines 63–70. Before the fix, `iterateClients` snapshots clients into strong references and invokes the callback for each snapshot entry. The callback can re-enter and remove a client from the live `WeakHashSet`. The patch adds `if (clients.contains(client))` before callback, skipping clients removed during prior callbacks. The commit adds a regression test `LayoutTests/fonts/font-face-load-crash.html`; the commit says the issue was fixed by using a smart pointer in `FontFace::loadForBindings` as well.

| Evidence question | Result |
|---|---|
| Component and class | WebKit WebCore CSS font-face client iteration / object lifetime; upstream UAF. |
| Vulnerable versus fixed source | Pre-fix callback is unconditional for snapshot entries. Post-fix callback is conditional on membership in the live client set. The commit also changes `FontFace::loadForBindings`. |
| Upstream confirmation | WebKit commit and regression test; Apple lists CVE-2026-43715 in its security advisory. |
| PS5 14.10 implementation | Unknown. No authorized Sony WebKit source/build comparison was located. |
| Offline reproduction | Source-level change is inspectable. A synthetic callback-removal model can illustrate the invariant, but cannot reproduce WebKit object lifetime or PS5 behavior. |
| Conclusion | **CONFIRMED UPSTREAM ONLY.** Do not label 14.10 affected or patched without a build/revision mapping. |

Primary sources: [WebKit fix](https://github.com/WebKit/WebKit/commit/5aedb82710ba578f), [Apple CVE-2026-43715 advisory](https://support.apple.com/en-us/149041).

## MetadataTable / UnlinkedMetadataTable

The supplied checkout describes a size multiplication and an intended JavaScriptCore metadata-table allocation. The reproducible arithmetic is `38,348,816 × 112 = 4,295,067,392`, which modulo 2^32 is 100,096. The updated toolkit models the exact uint32 limit and the first overflowing count without allocating memory. A separate checked-size model rejects multiplication results above `0xffffffff`; a bounds predicate tests index 0, index length, and negative indices.

| Evidence question | Result |
|---|---|
| Component | Reported JavaScriptCore `UnlinkedMetadataTable`; exact target implementation not present in the supplied repository. |
| Upstream CVE | CVE-2026-64784 is cited by the upstream WebKitGTK advisory; the exact fix/source comparison must be tied to an immutable source revision before claiming a version mapping. |
| 14.10 implementation | Unknown. No Sony JSC source or matching binary function is available. |
| Offline reproduction | Arithmetic and checked-boundary fixtures pass. They demonstrate arithmetic only, not an allocation, write, or heap corruption. |
| Device observation | Corrected V480 logged zero hits of 14 and no-corruption markers. An earlier compile/call sequence ends without definitive result; no independent crash cause or memory trace exists. |
| Conclusion | **POSSIBLE — INSUFFICIENT EVIDENCE** for target applicability; the specific `.length=81400` corruption assertion is **CONTRADICTED** by the corrected test. |

## Additional upstream candidates

The local audit cites CVE-2026-43705 (TransformStream), CVE-2026-7270 (`execve` arithmetic), and CVE-2026-45251 (descriptor/poll lifetime) with vendor advisories. For each, the upstream report is not enough to establish PS5 14.10 presence, unpatched status, caller reachability, or a useful primitive. Treat them as **CONFIRMED UPSTREAM ONLY** pending exact source/patch matching to Sony's fork and evidence of reachable behavior. CVE-2026-64784 likewise needs a reproducible immutable upstream fix comparison.

Official/public sources: [WebKitGTK 2026-0004](https://www.webkitgtk.org/security/WSA-2026-0004.html), [FreeBSD April advisory](https://lists.freebsd.org/archives/freebsd-security/2026-April/000448.html), [FreeBSD May advisory](https://lists.freebsd.org/archives/freebsd-security/2026-May/000453.html), [WebKitGTK 2026-0006](https://www.webkitgtk.org/security/WSA-2026-0006.html).
