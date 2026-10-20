# Upstream patch comparison and candidate status

**Phase 4 update:** [new source comparison](WEBKIT_TARGET_COMPATIBILITY.md) identifies the exact metadata overflow fix `97df94ead028cddcfc21e48ec6f2f72d25ec1662` and measures the old Sony metadata source. It also finds that the Sony TransformStream file already contains the relevant validation safeguards. These findings supersede earlier missing-source/patch statements below, while the 14.10 executable verdict remains unknown.

Audit: 20 October 2026. This phase independently compared Sony-published WebKit source files with six pinned upstream source pairs. Exact PS5 14.10 executable mapping remains unknown. The earlier statement that no Sony source comparison was available is superseded by the evidence below.

## CSSFontFace: two distinct safeguards

The actual mainline commit [`5aedb82710ba578f61501106e78f6b25b7f7a558`](https://github.com/WebKit/WebKit/commit/5aedb82710ba578f61501106e78f6b25b7f7a558) changes `CSSFontFace.cpp` and adds two regression-test files. Its message mentions an earlier `FontFace.cpp` smart-pointer fix, but that file is unchanged against parent `a7e4fdb9545042aef190cd469efb633e442fb43c`. The parent already contains the lifetime pin. This corrects the earlier report's claim that the same commit changed both functions.

The lifetime fix is directly visible in the GLib 2.52 backport [`f3d61dae1b61dfbd2fc0b01196b63f8769bca77e`](https://github.com/WebKit/WebKit/commit/f3d61dae1b61dfbd2fc0b01196b63f8769bca77e), relative to `d6dc8ef95ed7fb13ec3c1049520996408a174e5e`:

```diff
-    m_backing->load();
+    protect(m_backing)->load();
```

The client-iteration fix in main and the GLib follow-up [`f1fff08a99d77bac49c2500ece3fdcfac06c8f1c`](https://github.com/WebKit/WebKit/commit/f1fff08a99d77bac49c2500ece3fdcfac06c8f1c) changes the snapshot traversal:

```diff
-    for (auto& client : copyToVectorOf<Ref<CSSFontFaceClient>>(clients))
-        callback(client);
+    for (auto& client : copyToVectorOf<Ref<CSSFontFaceClient>>(clients)) {
+        if (clients.contains(client))
+            callback(client);
+    }
```

The stable maintainer states that the lifetime backport completed the security fix and the later guard resolved a stress-mode debug assertion. A missing membership guard alone must therefore not be equated with an unpatched memory-safety issue.

| Exact source revision | Backing pin | Membership guard | Source detector result |
|---|---|---|---|
| `0e722583a4d695c7b25f384c61fbf5b59b4c3146` | Absent | Absent | VULNERABLE IMPLEMENTATION — VERIFIED (source shape only) |
| `d6dc8ef95ed7fb13ec3c1049520996408a174e5e` | Absent | Absent | VULNERABLE IMPLEMENTATION — VERIFIED (source shape only) |
| `f3d61dae1b61dfbd2fc0b01196b63f8769bca77e` | Present | Absent | MODIFIED / AMBIGUOUS; documented lifetime security backport |
| `a7e4fdb9545042aef190cd469efb633e442fb43c` | Present | Absent | MODIFIED / AMBIGUOUS; main parent is not an unpatched lifetime baseline |
| `5aedb82710ba578f61501106e78f6b25b7f7a558` | Present | Present | PATCHED — VERIFIED (source safeguards) |
| `f1fff08a99d77bac49c2500ece3fdcfac06c8f1c` | Present | Present | PATCHED — VERIFIED (source safeguards) |
| Sony `WebKit_1400` sampled pair | Absent | Absent | Matches the `0e722…` files exactly; no executable verdict |

The two source files in each upstream pair were SHA-256 pinned and independently checked against GitHub Contents API blob identifiers (12 of 12 matches). Source/manifest hashes, original URLs, line citations and function classifications are in [WEBKIT_SOURCE_EVIDENCE.json](WEBKIT_SOURCE_EVIDENCE.json); the old/fixed output is [CSSFONTFACE_SOURCE_COMPARISON.json](CSSFONTFACE_SOURCE_COMPARISON.json). Hashes establish byte identity and API consistency, not a developer signature.

The [WebKitGTK/WPE advisory](https://webkitgtk.org/security/WSA-2026-0004.html) maps Bugzilla 313577 to CVE-2026-43715 and names affected versions before 2.52.5 for those ports. No universal introducing revision, complete branch range, or Sony firmware affected range was established. See [CSSFONTFACE_DEEP_ANALYSIS.md](CSSFONTFACE_DEEP_ANALYSIS.md) for ownership/reentry and [PS5_1410_WEBKIT_PROVENANCE.md](PS5_1410_WEBKIT_PROVENANCE.md) for the exact attribution limit.

## MetadataTable / UnlinkedMetadataTable

The supplied checkout describes a size multiplication and an intended JavaScriptCore metadata-table allocation. The reproducible arithmetic is `38,348,816 × 112 = 4,295,067,392`, which modulo 2^32 is 100,096. The updated toolkit models the exact uint32 limit and the first overflowing count without allocating memory. A separate checked-size model rejects multiplication results above `0xffffffff`; a bounds predicate tests index 0, index length, and negative indices.

| Evidence question | Result |
|---|---|
| Component | Reported JavaScriptCore `UnlinkedMetadataTable`; exact target implementation not present in the supplied repository. |
| Upstream CVE | CVE-2026-64784 is cited by the upstream WebKitGTK advisory; the exact fix/source comparison must be tied to an immutable source revision before claiming a version mapping. |
| 14.10 implementation | Unknown. Sony publishes source bundles, but the exact target JSC allocation function and executable correspondence were not established for this candidate. |
| Offline reproduction | Arithmetic and checked-boundary fixtures pass. They demonstrate arithmetic only, not an allocation, write, or heap corruption. |
| Device observation | Corrected V480 logged zero hits of 14 and no-corruption markers. An earlier compile/call sequence ends without definitive result; no independent crash cause or memory trace exists. |
| Conclusion | **POSSIBLE — INSUFFICIENT EVIDENCE** for target applicability; the specific `.length=81400` corruption assertion is **CONTRADICTED** by the corrected test. |

## Additional upstream candidates

The local audit cites CVE-2026-43705 (TransformStream), CVE-2026-7270 (`execve` arithmetic), and CVE-2026-45251 (descriptor/poll lifetime) with vendor advisories. For each, the upstream report is not enough to establish PS5 14.10 presence, unpatched status, caller reachability, or a useful primitive. Treat them as **CONFIRMED UPSTREAM ONLY** pending exact source/patch matching to Sony's fork and evidence of reachable behavior. CVE-2026-64784 likewise needs a reproducible immutable upstream fix comparison.

Official/public sources: [WebKitGTK 2026-0004](https://www.webkitgtk.org/security/WSA-2026-0004.html), [FreeBSD April advisory](https://lists.freebsd.org/archives/freebsd-security/2026-April/000448.html), [FreeBSD May advisory](https://lists.freebsd.org/archives/freebsd-security/2026-May/000453.html), [WebKitGTK 2026-0006](https://www.webkitgtk.org/security/WSA-2026-0006.html).
