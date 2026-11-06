@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"
title Ars Magna Defluens - Revue des 14 langues

REM Usage:
REM   Lancer_Revue_14_Langues.bat audit
REM   Lancer_Revue_14_Langues.bat repeat
REM   Lancer_Revue_14_Langues.bat compare
REM   Lancer_Revue_14_Langues.bat finalize "C:\...\review-decisions.json"
REM The pilot sources and RGL are never modified by audit or finalize.
set "ACTION=%~1"
if not defined ACTION set "ACTION=audit"
set "OUT=%USERPROFILE%\Downloads\Ars_Magna_Defluens\practical_pilot_runs"
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"
where py >nul 2>nul
if errorlevel 1 (set "PYTHON=python") else (set "PYTHON=py -3")

echo.
echo =============================================================
echo  ARS MAGNA DEFLUENS - VALIDATION CIBLEE DES 14 LANGUES

echo =============================================================
echo.
if /i "%ACTION%"=="audit" (
  %PYTHON% -m gf_wordbench.practical.review14 audit --batch-dir "%OUT%" --out-dir "%OUT%"
  if errorlevel 1 goto :error
  echo.
  echo Ouvrir le fichier Revue_14_langues.html du dossier defluens-review14-*.
  explorer "%OUT%"
  goto :success
)
if /i "%ACTION%"=="repeat" (
  echo Nouvel essai GF complet : 14 langues x 15 fonctions = 210 sondes.
  call "%~dp0Lancer_Campagne_Multilingue.bat" full Eng Fre Spa Ger Dut Swe Dan Nor Nno Fin Est Afr Ita Por
  if errorlevel 1 goto :error
  goto :success
)
if /i "%ACTION%"=="compare" (
  %PYTHON% -m gf_wordbench.practical.review14 compare --batch-dir "%OUT%" --out-dir "%OUT%"
  if errorlevel 1 goto :error
  explorer "%OUT%"
  goto :success
)
if /i "%ACTION%"=="finalize" (
  if "%~2"=="" (
    echo ERREUR : indiquer le chemin du JSON exporte depuis l'interface de revue.
    goto :error
  )
  %PYTHON% -m gf_wordbench.practical.review14 finalize --batch-dir "%OUT%" --out-dir "%OUT%" --decisions "%~2"
  if errorlevel 1 goto :error
  explorer "%OUT%"
  goto :success
)
echo ERREUR : action attendue : audit, repeat, compare ou finalize.
goto :error

:success
echo.
echo Termine. Aucune validation linguistique n'est automatiquement certifiee.
pause
exit /b 0
:error
echo.
echo Action interrompue. Les anciens rapports restent intacts.
pause
exit /b 1
