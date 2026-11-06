@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
where py >nul 2>nul
if errorlevel 1 (set "PYTHON=python") else (set "PYTHON=py -3")
echo.
echo =============================================================
echo  ARS MAGNA DEFLUENS - 31 SONDES CORRIGEES - v0.2.1
echo =============================================================
%PYTHON% -m gf_wordbench.practical.stabilization021 check
if errorlevel 1 exit /b 1
%PYTHON% -m gf_wordbench.practical.stabilization021 run
if errorlevel 1 (
 echo Certains tests ne sont pas confirmes. Envoie quand meme le ZIP de rapport.
 exit /b 1
)
echo.
echo Termine. ZIP partageable dans Downloads\Ars_Magna_Defluens\practical_pilot_runs
exit /b 0
