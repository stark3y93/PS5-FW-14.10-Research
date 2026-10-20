@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b %errorlevel%
if "%1"=="probe" goto probe
"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\Llvm\x64\bin\clang-cl.exe" /nologo /std:c++17 /Od /Zi /fsanitize=address /Fe:derived\phi_epoch_model.exe research\source-validation\phi_epoch_model.cpp
if errorlevel 1 exit /b %errorlevel%
derived\phi_epoch_model.exe
exit /b %errorlevel%
:probe
"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\Llvm\x64\bin\clang-cl.exe" /nologo /Od /Zi /fsanitize=address /Fe:derived\asan_probe.exe research\source-validation\asan_probe.cpp
if errorlevel 1 exit /b %errorlevel%
derived\asan_probe.exe
exit /b %errorlevel%
