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

REM Verification de conda
where conda >nul 2>&1
if %errorlevel% neq 0 (
    echo ERREUR: Conda n'est pas detecte
    echo Veuillez ouvrir "Anaconda Prompt" et lancer ce script depuis la
    pause
    exit /b 1
)

REM Verification de l'environnement
call conda env list | find "automatisation" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERREUR: L'environnement "automatisation" n'existe pas
    echo.
    echo Veuillez d'abord executer un des scripts d'installation :
    echo   - setup_env_cpu.bat (pour CPU uniquement)
    echo   - setup_env_gpu.bat (pour GPU avec CUDA 12.1)
    echo.
    pause
    exit /b 1
)

echo Activation de l'environnement "automatisation"...
call conda activate automatisation
if %errorlevel% neq 0 (
    echo ERREUR: Impossible d'activer l'environnement
    pause
    exit /b 1
)

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
