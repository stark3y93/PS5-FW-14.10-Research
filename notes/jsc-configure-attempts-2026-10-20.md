# Unmodified JavaScriptCore PC build preflight

Source: official Sony `WebKit_1400.zip`, SHA-256 `e645974579c88ec09c3036ce882fcaea2b0380f9ae4596b163811501d3be9db0`. Selected root CMake files plus unmodified `Source/JavaScriptCore`, `Source/WTF`, `Source/bmalloc`, `Source/cmake` and `Tools/Scripts` were extracted to ignored `derived/jsc-build-source`. Extraction selected 6,482 files totaling 82,177,253 uncompressed bytes; no file was edited. This is a build subset, not the entire archive. Build output was directed to ignored `derived/jsc-build`. No PS5 or firmware binary was involved.

Host: Windows, Visual Studio 2022 Community x64 MSVC 14.38.33130, bundled CMake 3.31 and Ninja. Configuration flags were `-G Ninja -DPORT=JSCOnly -DENABLE_TOOLS=OFF -DENABLE_API_TESTS=OFF`; the second attempt also passed `-DPERL_EXECUTABLE="C:\Program Files\Git\usr\bin\perl.exe"`. Both invocations started after `vcvars64.bat`. Full raw CMake outputs remain local in ignored `derived/jsc-configure.log` and `derived/jsc-configure-2.log`.

| Attempt | Key diagnostic | Exit | Interpretation |
|---|---|---:|---|
| 1 | `Could NOT find Perl (missing: PERL_EXECUTABLE) (Required is at least version "5.10.0")` at `Source/cmake/WebKitCommon.cmake:183` | 1 | Configuration stopped before build generation. |
| 2 | `Found Perl ... 5.38.2`; `Found PerlModules ... English FindBin JSON::PP`; `Could NOT find Ruby (missing: Ruby_EXECUTABLE Ruby_INCLUDE_DIR Ruby_LIBRARY) (Required is at least version "2.5")`; `Ruby 2.5 or higher is required` at `WebKitCommon.cmake:196` | 1 | Perl prerequisite cleared; Ruby prerequisite stopped configuration. |

No JavaScriptCore object file, executable, regression test or sanitizer-instrumented engine was produced. Later build dependencies remain unchecked. The separate AddressSanitizer graph model is original synthetic code and cannot substitute for an engine-level test.
