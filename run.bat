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

REM Initialiser conda pour ce script (essayer plusieurs emplacements)
call "C:\ia\anaconda\Scripts\activate.bat" >nul 2>&1
call "%USERPROFILE%\anaconda3\Scripts\activate.bat" >nul 2>&1
call "%USERPROFILE%\miniconda3\Scripts\activate.bat" >nul 2>&1
call "%LOCALAPPDATA%\anaconda3\Scripts\activate.bat" >nul 2>&1
call "C:\ProgramData\anaconda3\Scripts\activate.bat" >nul 2>&1

REM Essayer d'activer directement l'environnement
echo Activation de l'environnement "automatisation"...
call conda activate automatisation 2>nul
if %errorlevel% neq 0 (
    echo.
    echo ERREUR: Impossible d'activer l'environnement "automatisation"
    echo.
    echo L'environnement n'existe peut-etre pas. Executez d'abord :
    echo   - setup_env_intel.bat (recommande pour Intel + Android)
    echo   - setup_env_cpu.bat (pour CPU uniquement)
    echo   - setup_env_gpu.bat (pour GPU NVIDIA avec CUDA 12.1)
    echo.
    pause
    exit /b 1
)

echo OK - Environnement active
echo.
echo Lancement de l'automatisation...
echo Appuyez sur CTRL+C pour arreter proprement
echo.
echo ========================================================================
echo.

python main.py %*

echo.
echo ========================================================================
echo   Automatisation terminee
echo ========================================================================
pause
