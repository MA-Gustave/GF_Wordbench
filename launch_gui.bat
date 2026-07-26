@echo off
setlocal EnableExtensions DisableDelayedExpansion

rem GF Wordbench GUI launcher.
rem This wrapper only resolves a Python entrypoint, forwards arguments unchanged,
rem and returns the exact child-process exit code.

set "GF_WORDBENCH_ROOT=%~dp0"
set "GF_WORDBENCH_VENV_SCRIPTS=%GF_WORDBENCH_ROOT%.venv\Scripts"

if exist "%GF_WORDBENCH_VENV_SCRIPTS%\gf-wordbench-gui.exe" goto run_venv_entrypoint
if exist "%GF_WORDBENCH_VENV_SCRIPTS%\pythonw.exe" goto run_venv_pythonw
if exist "%GF_WORDBENCH_VENV_SCRIPTS%\python.exe" goto run_venv_python

where gf-wordbench-gui.exe >nul 2>nul
if not errorlevel 1 goto run_path_entrypoint

where pyw.exe >nul 2>nul
if not errorlevel 1 goto run_pyw

where pythonw.exe >nul 2>nul
if not errorlevel 1 goto run_pythonw

where py.exe >nul 2>nul
if not errorlevel 1 goto run_py

where python.exe >nul 2>nul
if not errorlevel 1 goto run_python

echo GF Wordbench GUI could not be started. 1>&2
echo No repository virtual environment, installed gf-wordbench-gui command, 1>&2
echo or supported Python interpreter was found. 1>&2
echo Install the project with: 1>&2
echo   py -m pip install -e "%GF_WORDBENCH_ROOT%[dev]" 1>&2
exit /b 3

:run_venv_entrypoint
"%GF_WORDBENCH_VENV_SCRIPTS%\gf-wordbench-gui.exe" %*
exit /b %errorlevel%

:run_venv_pythonw
"%GF_WORDBENCH_VENV_SCRIPTS%\pythonw.exe" -m gf_wordbench.entrypoints.gui.main %*
exit /b %errorlevel%

:run_venv_python
"%GF_WORDBENCH_VENV_SCRIPTS%\python.exe" -m gf_wordbench.entrypoints.gui.main %*
exit /b %errorlevel%

:run_path_entrypoint
gf-wordbench-gui.exe %*
exit /b %errorlevel%

:run_pyw
pyw.exe -3 -m gf_wordbench.entrypoints.gui.main %*
exit /b %errorlevel%

:run_pythonw
pythonw.exe -m gf_wordbench.entrypoints.gui.main %*
exit /b %errorlevel%

:run_py
py.exe -3 -m gf_wordbench.entrypoints.gui.main %*
exit /b %errorlevel%

:run_python
python.exe -m gf_wordbench.entrypoints.gui.main %*
exit /b %errorlevel%
