# CSSFontFace lifetime and reentrancy analysis

Audit: 20 October 2026. **PS5 14.10 classification: UNKNOWN.** Sony's published `WebKit_1400` source contains the old implementation; an exact production browser build correspondence has not been established. Source evidence, synthetic behavior, and firmware impact are different findings.

## Source and ownership sequence

The independently acquired Sony files `Source/WebCore/css/CSSFontFace.cpp` and `FontFace.cpp` exactly match those files at upstream [`0e722583a4d695c7b25f384c61fbf5b59b4c3146`](https://github.com/WebKit/WebKit/tree/0e722583a4d695c7b25f384c61fbf5b59b4c3146). Their full SHA-256 values and acquisition metadata are in [WEBKIT_SOURCE_EVIDENCE.json](WEBKIT_SOURCE_EVIDENCE.json). This proves file identity, not whole-tree or executable identity. Five of eight selected Sony files match the pinned upstream files; platform options, user-agent code and CSSFontFace.h differ. The header removes `virtual` from the destructor declaration, so no ABI/layout equivalence is inferred.

| Location in the matched source | Observed implementation | Implication |
|---|---|---|
| [FontFace.h:109](https://github.com/WebKit/WebKit/blob/0e722583a4d695c7b25f384c61fbf5b59b4c3146/Source/WebCore/css/FontFace.h#L109) | `m_backing` is a `Ref<CSSFontFace>`. | The wrapper owns its current backing object. |
| [FontFace.cpp:324](https://github.com/WebKit/WebKit/blob/0e722583a4d695c7b25f384c61fbf5b59b4c3146/Source/WebCore/css/FontFace.cpp#L324) | `adopt` removes the old client link, assigns a new backing, and adds the new client link. | Reentrant adoption can release the old backing reference. |
| [FontFace.cpp:358](https://github.com/WebKit/WebKit/blob/0e722583a4d695c7b25f384c61fbf5b59b4c3146/Source/WebCore/css/FontFace.cpp#L358) | `loadForBindings` calls `m_backing->load()` without a temporary strong reference. | The backing is not pinned across a potentially reentrant call. |
| [CSSFontFace.cpp:701](https://github.com/WebKit/WebKit/blob/0e722583a4d695c7b25f384c61fbf5b59b4c3146/Source/WebCore/css/CSSFontFace.cpp#L701) | `load` calls `pump`, whose local-source path can change status synchronously. | A load can invoke client notifications before returning. |
| [CSSFontFace.cpp:571](https://github.com/WebKit/WebKit/blob/0e722583a4d695c7b25f384c61fbf5b59b4c3146/Source/WebCore/css/CSSFontFace.cpp#L571) | `setStatus` calls clients and subsequently updates `m_status`. | The subject must remain alive while callbacks execute and the method resumes. |
| [FontFace.cpp:332](https://github.com/WebKit/WebKit/blob/0e722583a4d695c7b25f384c61fbf5b59b4c3146/Source/WebCore/css/FontFace.cpp#L332) | A successful state notification resolves the loaded promise with the wrapper. | Promise resolution can inspect a thenable property and invoke a getter synchronously. |
| [CSSFontFace.cpp:55](https://github.com/WebKit/WebKit/blob/0e722583a4d695c7b25f384c61fbf5b59b4c3146/Source/WebCore/css/CSSFontFace.cpp#L55) | `iterateClients` snapshots weak-set members as strong client references and calls every snapshot member. | Removal from the live set does not remove an entry from the snapshot. |

The two problems must be described separately. Holding strong **client** references in the snapshot does not necessarily retain the original **backing face** if a wrapper adopts another backing. Conversely, calling a still-alive client after it has left the live set is a membership/invariant failure; it is not by itself proof that the client pointer was freed.

The public regression test exercises synchronous script reentry through promise resolution while font/style state changes. ECMAScript's [Promise Resolve Functions](https://tc39.es/ecma262/multipage/control-abstraction-objects.html#sec-promise-resolve-functions) obtains the `then` property before scheduling thenable invocation; a getter can therefore run during resolution. Source inspection supports the lifetime hazard and stale-membership sequence. This audit did not trace a target heap or demonstrate an actual WebKit memory fault.

## Exact patch history

- [`f3d61dae1b61dfbd2fc0b01196b63f8769bca77e`](https://github.com/WebKit/WebKit/commit/f3d61dae1b61dfbd2fc0b01196b63f8769bca77e), GLib 2.52, 2 July 2026: changes the backing call to `protect(m_backing)->load()`. Its parent is `d6dc8ef95ed7fb13ec3c1049520996408a174e5e`. The temporary reference retains the selected backing across reentry.
- [`5aedb82710ba578f61501106e78f6b25b7f7a558`](https://github.com/WebKit/WebKit/commit/5aedb82710ba578f61501106e78f6b25b7f7a558), main, 3 July 2026: adds a live-membership check before each copied client callback. Its parent `a7e4fdb9545042aef190cd469efb633e442fb43c` **already has the backing pin**. `FontFace.cpp` is byte-identical in this parent and child.
- [`f1fff08a99d77bac49c2500ece3fdcfac06c8f1c`](https://github.com/WebKit/WebKit/commit/f1fff08a99d77bac49c2500ece3fdcfac06c8f1c), GLib 2.52, 3 July 2026: adds the same membership guard. The maintainer explicitly describes the preceding lifetime fix as security-complete and the remaining failure as a stress-mode debug assertion in `CSSFontFaceSet::fontStateChanged`.

Correction to the earlier report: the actual `5aedb827…` diff changes `CSSFontFace.cpp` and adds two test files. It does **not** also change `FontFace.cpp`, despite mentioning that function and an earlier smart-pointer fix in its message. The branch history and file bytes resolve that apparent conflict.

The original Safari identifier `305413.775@safari-7624-branch` and abbreviated `d90247302507` are attributed in the backport metadata. The API lookup of that abbreviated revision returned HTTP 422 in this audit; its original source delta was not independently fetched. The complete GLib backport was fetched and inspected instead.

## Supported ranges and remaining uncertainty

The [WebKitGTK/WPE advisory](https://webkitgtk.org/security/WSA-2026-0004.html) associates CVE-2026-43715 with Bugzilla 313577 and names versions before 2.52.5 for those products. This is not a Sony version range. Exact inspected examples establish old source at `0e722…`, an unprotected GLib parent at `d6dc8…`, a lifetime-only backport at `f3d61…`, and both safeguards in the two fixed reference snapshots. The introducing revision and every affected branch were not established.

Sony's “14.00 -” publication is meaningful vendor source provenance. The two files lack both safeguards and match the older upstream files exactly. It remains possible for the executable to contain a backport, another component, or production changes absent from the published snapshot. No authorized 14.10 browser binary, signed component build record, or engine-level result resolves that distinction here.

## Offline experiments and detector semantics

The synthetic models show that removing a future client leaves it in an unguarded snapshot, that the guard skips it, that newly added clients are not in the existing snapshot, and that results depend on callback order. The lifetime model shows a temporary owner keeping the backing alive until the reentrant call returns. These are logical state transitions, not sanitizer traces or real memory corruption.

The detector uses pinned full-file hashes **and** exact recognized function shapes for verified source classifications. Familiar snippets in changed files, mixed safeguards, duplicate functions, or uncertain implementations remain `MODIFIED / AMBIGUOUS`. Missing files, truncation, manifest/version conflicts and hash failures cannot yield a verified result. A lifetime-only backport is not labeled an unpatched UAF. Every PS5 14.10 output remains `INSUFFICIENT EVIDENCE` because caller labels cannot authenticate a Sony build.

See [CSSFONTFACE_SOURCE_COMPARISON.json](CSSFONTFACE_SOURCE_COMPARISON.json) for the reproducible old/fixed comparison and [PS5_1410_WEBKIT_PROVENANCE.md](PS5_1410_WEBKIT_PROVENANCE.md) for target attribution limits.
