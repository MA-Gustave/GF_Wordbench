@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"
title Ars Magna Defluens - Pilote WordBench

REM Arguments: code de langue parmi les 20 pilotes  [smoke|full|check]
REM Double-clic : Eng smoke uniquement (une seule capacite).
set "LANGUE=%~1"
if not defined LANGUE set "LANGUE=Eng"
set "SCOPE=%~2"
if not defined SCOPE set "SCOPE=smoke"


set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
where py >nul 2>nul
if errorlevel 1 (
    set "PYTHON=python"
) else (
    set "PYTHON=py -3"
)

set "GF_EXE=C:\mycode\Grammatical-Framework\gf-3.12-windows\gf.exe"
set "RGL_ROOT=C:\mycode\Grammatical-Framework\gf-rgl"
set "PILOT_OUTPUT=%USERPROFILE%\Downloads\Ars_Magna_Defluens\practical_pilot_runs"

echo ============================================================
echo Ars Magna Defluens - Validation pratique WordBench
echo Langue : %LANGUE%   Portee : %SCOPE%
echo ============================================================
echo.

%PYTHON% -m gf_wordbench.practical.pilot check --language "%LANGUE%"
if errorlevel 1 goto :error

if /I "%SCOPE%"=="check" goto :success

if not exist "%GF_EXE%" (
  echo ERREUR: gf.exe absent de %GF_EXE%
  goto :error
)
if not exist "%RGL_ROOT%\src\" (
  echo ERREUR: racine de RGL absente : %RGL_ROOT%
  goto :error
)

echo.
echo Test GF reel en cours. Les resultats ne sont PAS des golds approuves.
echo Rapports : %PILOT_OUTPUT%
echo ZIP de partage : creation automatique en fin de test
echo.

if /I "%SCOPE%"=="full" (
  %PYTHON% -m gf_wordbench.practical.pilot run --language "%LANGUE%" --gf-executable "%GF_EXE%" --rgl-root "%RGL_ROOT%" --output-root "%PILOT_OUTPUT%" --export-zip --timeout 120
) else if /I "%SCOPE%"=="smoke" (
  %PYTHON% -m gf_wordbench.practical.pilot run --language "%LANGUE%" --scenario factual-present --gf-executable "%GF_EXE%" --rgl-root "%RGL_ROOT%" --output-root "%PILOT_OUTPUT%" --export-zip --timeout 120
) else (
  echo ERREUR: portee possible: smoke, full ou check.
  goto :error
)
if errorlevel 1 goto :error

:success
echo.
echo Termine. Pour les 15 scenarios: Lancer_Pilote_Pratique.bat Eng full
echo Dossier de resultats : %PILOT_OUTPUT%
echo Rapport JSON : defluens-pilot-*\pilot_run.json
echo ZIP partageable : %PILOT_OUTPUT%\defluens-pilot-*.zip
echo.
pause
exit /b 0

:error
echo.
echo Validation terminee avec une erreur. Consultez pilot_run.json et les journaux.
echo Aucun resultat linguistique non revu n'est marque "reussi".
echo.
pause
exit /b 1
