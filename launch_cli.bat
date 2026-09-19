@echo off
setlocal EnableExtensions DisableDelayedExpansion

set "GF_WORDBENCH_ROOT=%~dp0"
set "GF_WORDBENCH_LOCAL_CLI=%GF_WORDBENCH_ROOT%.venv\Scripts\gf-wordbench.exe"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

pushd "%GF_WORDBENCH_ROOT%" >nul 2>&1
if errorlevel 1 goto :repository_error

if not exist "%GF_WORDBENCH_LOCAL_CLI%" goto :missing_cli

"%GF_WORDBENCH_LOCAL_CLI%" %*
set "GF_WORDBENCH_EXIT_CODE=%ERRORLEVEL%"
goto :finish

:missing_cli
echo ERROR: Wordbench CLI environment is unavailable. 1>&2
echo Expected local entrypoint: "%GF_WORDBENCH_LOCAL_CLI%" 1>&2
echo Install the project into the repository-local .venv environment. 1>&2
set "GF_WORDBENCH_EXIT_CODE=3"
goto :finish

:repository_error
echo ERROR: Wordbench CLI cannot access its repository directory. 1>&2
echo Repository directory: "%GF_WORDBENCH_ROOT%" 1>&2
exit /b 3

:finish
popd
exit /b %GF_WORDBENCH_EXIT_CODE%