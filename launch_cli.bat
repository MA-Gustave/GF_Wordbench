@echo off
setlocal EnableExtensions DisableDelayedExpansion

set "GF_WORDBENCH_ROOT=%~dp0"
set "GF_WORDBENCH_LOCAL_CLI=%GF_WORDBENCH_ROOT%.venv\Scripts\gf-wordbench.exe"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

pushd "%GF_WORDBENCH_ROOT%" >nul 2>&1
if errorlevel 1 (
    >&2 echo GF Wordbench launcher error: unable to access repository directory "%GF_WORDBENCH_ROOT%".
    exit /b 3
)

if exist "%GF_WORDBENCH_LOCAL_CLI%" (
    "%GF_WORDBENCH_LOCAL_CLI%" %*
    set "GF_WORDBENCH_EXIT_CODE=%ERRORLEVEL%"
    popd
    exit /b %GF_WORDBENCH_EXIT_CODE%
)

where.exe gf-wordbench.exe >nul 2>&1
if not errorlevel 1 (
    gf-wordbench.exe %*
    set "GF_WORDBENCH_EXIT_CODE=%ERRORLEVEL%"
    popd
    exit /b %GF_WORDBENCH_EXIT_CODE%
)

>&2 echo GF Wordbench launcher error: the canonical CLI executable was not found.
>&2 echo Expected local executable: "%GF_WORDBENCH_LOCAL_CLI%"
>&2 echo Install the project into .venv or make gf-wordbench.exe available on PATH.
popd
exit /b 9009
