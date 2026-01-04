@echo off
REM ============================================================================
REM Script de lancement rapide
REM Framework d'automatisation Mafia City
REM ============================================================================

echo.
echo ========================================================================
echo   Lancement de l'automatisation Mafia City
echo ========================================================================
echo.

REM Chercher Python dans l'environnement automatisation
set "PYTHON_ENV="

REM Vérifier les emplacements courants de conda
if exist "C:\ia\anaconda\envs\automatisation\python.exe" (
    set "PYTHON_ENV=C:\ia\anaconda\envs\automatisation\python.exe"
    goto :found
)
if exist "%USERPROFILE%\anaconda3\envs\automatisation\python.exe" (
    set "PYTHON_ENV=%USERPROFILE%\anaconda3\envs\automatisation\python.exe"
    goto :found
)
if exist "%USERPROFILE%\miniconda3\envs\automatisation\python.exe" (
    set "PYTHON_ENV=%USERPROFILE%\miniconda3\envs\automatisation\python.exe"
    goto :found
)
if exist "%LOCALAPPDATA%\anaconda3\envs\automatisation\python.exe" (
    set "PYTHON_ENV=%LOCALAPPDATA%\anaconda3\envs\automatisation\python.exe"
    goto :found
)
if exist "C:\ProgramData\anaconda3\envs\automatisation\python.exe" (
    set "PYTHON_ENV=C:\ProgramData\anaconda3\envs\automatisation\python.exe"
    goto :found
)

REM Environnement non trouvé
echo ERREUR: L'environnement "automatisation" n'a pas ete trouve.
echo.
echo Executez d'abord un des scripts d'installation :
echo   - setup_env_intel.bat (recommande pour Intel + Android)
echo   - setup_env_cpu.bat (pour CPU uniquement)
echo   - setup_env_gpu.bat (pour GPU NVIDIA avec CUDA 12.1)
echo.
pause
exit /b 1

:found
echo Environnement trouve: %PYTHON_ENV%
echo.
echo Lancement de l'automatisation...
echo Appuyez sur CTRL+C pour arreter proprement
echo.
echo ========================================================================
echo.

"%PYTHON_ENV%" main.py %*

echo.
echo ========================================================================
echo   Automatisation terminee
echo ========================================================================
pause
