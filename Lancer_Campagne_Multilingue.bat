@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"
title Ars Magna Defluens - Campagne WordBench multilingue

REM Usage : Lancer_Campagne_Multilingue.bat [smoke^|full^|check] [Langue1 Langue2 ...]
REM Par defaut: smoke des 20 langues preparees; un scenario par langue.
REM Pour les 300 sondes: Lancer_Campagne_Multilingue.bat full
set "MODE=%~1"
if not defined MODE set "MODE=smoke"
if /I not "%MODE%"=="smoke" if /I not "%MODE%"=="full" if /I not "%MODE%"=="check" (
  echo ERREUR : mode smoke, full ou check.
  goto :error
)
shift
set "LANGS="
:collect_langs
if "%~1"=="" goto :langs_ready
set "LANGS=%LANGS% %~1"
shift
goto :collect_langs
:langs_ready

set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
where py >nul 2>nul
if errorlevel 1 (set "PYTHON=python") else (set "PYTHON=py -3")
set "GF_EXE=C:\mycode\Grammatical-Framework\gf-3.12-windows\gf.exe"
set "RGL_ROOT=C:\mycode\Grammatical-Framework\gf-rgl"
set "PILOT_OUTPUT=%USERPROFILE%\Downloads\Ars_Magna_Defluens\practical_pilot_runs"

echo ============================================================
echo ARS MAGNA DEFLUENS : CAMPAGNE MULTILINGUE - %MODE%
echo ============================================================
echo 20 langues preparees, 15 capacites chacune.
echo Les phrases restent des candidates NON approuvees.
echo Rapports et ZIP : %PILOT_OUTPUT%
echo.
if /I "%MODE%"=="check" (
  if defined LANGS (
    %PYTHON% -m gf_wordbench.practical.batch check --languages %LANGS%
  ) else (
    %PYTHON% -m gf_wordbench.practical.batch check
  )
  if errorlevel 1 goto :error
  goto :success
)

if not exist "%GF_EXE%" (
  echo ERREUR: gf.exe absent : %GF_EXE%
  goto :error
)
if not exist "%RGL_ROOT%\src\" (
  echo ERREUR: dossier gf-rgl\src introuvable : %RGL_ROOT%
  goto :error
)

REM Limite par sonde 90 s ; limite globale 45 min, entre langues.
if defined LANGS (
  %PYTHON% -m gf_wordbench.practical.batch run --mode "%MODE%" --gf-executable "%GF_EXE%" --rgl-root "%RGL_ROOT%" --output-root "%PILOT_OUTPUT%" --timeout 90 --max-minutes 45 --languages %LANGS%
) else (
  %PYTHON% -m gf_wordbench.practical.batch run --mode "%MODE%" --gf-executable "%GF_EXE%" --rgl-root "%RGL_ROOT%" --output-root "%PILOT_OUTPUT%" --timeout 90 --max-minutes 45
)
if errorlevel 1 goto :error
:success
echo.
echo Rapports termines. Trouver le dernier defluens-batch-*.zip dans Downloads.
echo.
pause
exit /b 0
:error
echo.
echo Des erreurs ont ete detectees. Les rapports partiels sont conserves.
echo Ouvrir batch_summary.json / batch_summary.csv dans le dernier dossier.
echo.
pause
exit /b 1
