@echo off
REM ============================================================================
REM Script d'installation - Environnement CPU
REM Framework d'automatisation Mafia City
REM ============================================================================

echo.
echo ========================================================================
echo   Installation de l'environnement AUTOMATISATION (CPU)
echo ========================================================================
echo.
echo Ce script va :
echo   - Installer scrcpy et ADB (pour controle Android)
echo   - Creer un environnement conda nomme "automatisation"
echo   - Installer Python 3.12
echo   - Installer PyTorch (version CPU)
echo   - Installer toutes les dependances (OpenCV, EasyOCR, etc.)
echo.
echo Appuyez sur une touche pour continuer ou CTRL+C pour annuler...
pause >nul

echo.
echo [1/7] Installation de scrcpy et ADB...
echo.

REM Verifier si winget est disponible
where winget >nul 2>&1
if %errorlevel% neq 0 (
    echo AVERTISSEMENT: winget n'est pas disponible
    echo scrcpy ne sera pas installe automatiquement.
    echo Installez-le manuellement depuis: https://github.com/Genymobile/scrcpy/releases
    echo.
) else (
    REM Installer scrcpy via winget (inclut ADB)
    echo Installation de scrcpy via winget...
    winget install Genymobile.scrcpy --accept-package-agreements --accept-source-agreements -h

    if %errorlevel% neq 0 (
        echo Note: scrcpy est peut-etre deja installe.
    )
)

REM Verifier que scrcpy est installe
where scrcpy >nul 2>&1
if %errorlevel% neq 0 (
    echo AVERTISSEMENT: scrcpy n'est pas dans le PATH
    echo Apres installation, fermez et rouvrez Anaconda Prompt.
) else (
    echo OK - scrcpy detecte
)

REM Verifier ADB
where adb >nul 2>&1
if %errorlevel% neq 0 (
    echo AVERTISSEMENT: adb n'est pas dans le PATH
) else (
    echo OK - adb detecte
)

echo.
echo [2/7] Verification de conda...
where conda >nul 2>&1
if %errorlevel% neq 0 (
    echo ERREUR: Conda n'est pas installe ou n'est pas dans le PATH
    echo Veuillez installer Anaconda ou Miniconda depuis https://www.anaconda.com/
    pause
    exit /b 1
)
echo OK - Conda detecte

echo.
echo [3/7] Suppression de l'environnement existant (si present)...
call conda env remove -n automatisation -y >nul 2>&1
echo OK

echo.
echo [4/7] Creation de l'environnement conda avec Python 3.12...
call conda create -n automatisation python=3.12 -y
if %errorlevel% neq 0 (
    echo ERREUR: Echec de creation de l'environnement
    pause
    exit /b 1
)
echo OK

echo.
echo [5/7] Activation de l'environnement...
call conda activate automatisation
if %errorlevel% neq 0 (
    echo ERREUR: Impossible d'activer l'environnement
    pause
    exit /b 1
)
echo OK

echo.
echo [6/7] Installation de PyTorch (CPU)...
echo Cette etape peut prendre plusieurs minutes...
call pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
if %errorlevel% neq 0 (
    echo ERREUR: Echec de l'installation de PyTorch
    pause
    exit /b 1
)
echo OK

echo.
echo [7/7] Installation des dependances du projet...
echo Cette etape peut prendre plusieurs minutes...

REM Installation des dependances principales
echo   - mss (capture d'ecran)...
call pip install "mss>=9.0.0"

echo   - opencv-python (vision par ordinateur)...
call pip install "opencv-python>=4.8.0"

echo   - Pillow (traitement d'images)...
call pip install "Pillow>=10.0.0"

echo   - numpy (calculs numeriques)...
call pip install "numpy>=1.24.0,<2.3.0"

echo   - pyautogui (automatisation)...
call pip install "pyautogui>=0.9.54"

echo   - pywin32 (integration Windows)...
call pip install "pywin32>=306"

echo   - pynput (detection clavier/souris)...
call pip install "pynput>=1.7.6"

echo   - EasyOCR (reconnaissance de texte - CPU)...
call pip install "easyocr>=1.7.0"

echo   - pytest (tests unitaires)...
call pip install "pytest>=7.4.0"

echo   - pytest-cov (couverture de code)...
call pip install "pytest-cov>=4.1.0"

if %errorlevel% neq 0 (
    echo ERREUR: Echec de l'installation des dependances
    pause
    exit /b 1
)
echo OK

echo.
echo ========================================================================
echo   INSTALLATION TERMINEE AVEC SUCCES !
echo ========================================================================
echo.
echo Environnement : automatisation (CPU)
echo Python        : 3.12
echo PyTorch       : CPU uniquement
echo OCR           : EasyOCR (CPU)
echo Scrcpy/ADB    : Installe via winget
echo Tests         : pytest + pytest-cov
echo.
echo IMPORTANT: Si scrcpy/adb ne sont pas reconnus,
echo            FERMEZ et ROUVREZ Anaconda Prompt.
echo.
echo Pour utiliser cet environnement :
echo   1. Ouvrez un nouveau terminal Anaconda Prompt
echo   2. Tapez : conda activate automatisation
echo   3. Connectez votre telephone Android en USB (mode debogage active)
echo   4. Lancez : python main.py
echo.
echo Ou double-cliquez simplement sur run.bat !
echo.
echo ========================================================================
pause
