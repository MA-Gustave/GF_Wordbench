@echo off
setlocal EnableExtensions DisableDelayedExpansion

rem GF Wordbench GUI launcher.
rem Resolve only the documented GUI entrypoint, forward the original argument
rem vector unchanged, and return the exact child process exit code.

set "GF_WORDBENCH_ROOT=%~dp0"
set "GF_WORDBENCH_VENV_SCRIPTS=%GF_WORDBENCH_ROOT%.venv\Scripts"
set "GF_WORDBENCH_LOCAL_GUI=%GF_WORDBENCH_VENV_SCRIPTS%\gf-wordbench-gui.exe"
set "GF_WORDBENCH_LOCAL_PYTHONW=%GF_WORDBENCH_VENV_SCRIPTS%\pythonw.exe"
set "GF_WORDBENCH_LOCAL_PYTHON=%GF_WORDBENCH_VENV_SCRIPTS%\python.exe"
set "GF_WORDBENCH_EXIT_CODE=0"

pushd "%GF_WORDBENCH_ROOT%" >nul 2>&1
if errorlevel 1 goto :repository_error

if exist "%GF_WORDBENCH_LOCAL_GUI%" goto :run_local_entrypoint
if exist "%GF_WORDBENCH_LOCAL_PYTHONW%" goto :run_local_pythonw
if exist "%GF_WORDBENCH_LOCAL_PYTHON%" goto :run_local_python

where.exe gf-wordbench-gui.exe >nul 2>&1
if not errorlevel 1 goto :run_path_entrypoint

goto :environment_error

:run_local_entrypoint
"%GF_WORDBENCH_LOCAL_GUI%" %*
set "GF_WORDBENCH_EXIT_CODE=%ERRORLEVEL%"
goto :finish

:run_local_pythonw
"%GF_WORDBENCH_LOCAL_PYTHONW%" -m gf_wordbench.entrypoints.gui.main %*
set "GF_WORDBENCH_EXIT_CODE=%ERRORLEVEL%"
goto :finish

:run_local_python
"%GF_WORDBENCH_LOCAL_PYTHON%" -m gf_wordbench.entrypoints.gui.main %*
set "GF_WORDBENCH_EXIT_CODE=%ERRORLEVEL%"
goto :finish

:run_path_entrypoint
gf-wordbench-gui.exe %*
set "GF_WORDBENCH_EXIT_CODE=%ERRORLEVEL%"
goto :finish

:environment_error
>&2 echo ERROR: GF Wordbench GUI environment is unavailable.
>&2 echo Expected local executable: "%GF_WORDBENCH_LOCAL_GUI%"
>&2 echo Expected local interpreter: "%GF_WORDBENCH_LOCAL_PYTHONW%"
>&2 echo Install the project into ".venv" or make gf-wordbench-gui.exe available on PATH.
set "GF_WORDBENCH_EXIT_CODE=9009"
goto :finish

:repository_error
>&2 echo ERROR: GF Wordbench GUI cannot access its repository directory.
>&2 echo Repository directory: "%GF_WORDBENCH_ROOT%"
exit /b 3

:finish
popd
exit /b %GF_WORDBENCH_EXIT_CODE%