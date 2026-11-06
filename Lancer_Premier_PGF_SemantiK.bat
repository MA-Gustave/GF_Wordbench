@echo off
setlocal
cd /d "%~dp0"
set "GF_EXE=C:\mycode\Grammatical-Framework\gf-3.12-windows\gf.exe"
set "SA_ROOT=C:\mycode\SemantiK_Architect\SemantiK_Architect"
py -3 tools\build_semantik_profile3_candidate.py --semantik-root "%SA_ROOT%" --gf-exe "%GF_EXE%" --force
if errorlevel 1 (
  echo.
  echo Le PGF candidat n'a pas ete construit. Voir les erreurs ci-dessus.
  pause
  exit /b 2
)
echo.
echo PGF candidat construit dans Downloads\Ars_Magna_Defluens\semantik_candidates.
pause
