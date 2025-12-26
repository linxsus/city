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
echo   - Creer un environnement conda nomme "automatisation"
echo   - Installer Python 3.12
echo   - Installer PyTorch (version CPU)
echo   - Installer toutes les dependances (OpenCV, EasyOCR, etc.)
echo.
echo Appuyez sur une touche pour continuer ou CTRL+C pour annuler...
pause >nul

echo.
echo [1/6] Verification de conda...
where conda >nul 2>&1
if %errorlevel% neq 0 (
    echo ERREUR: Conda n'est pas installe ou n'est pas dans le PATH
    echo Veuillez installer Anaconda ou Miniconda depuis https://www.anaconda.com/
    pause
    exit /b 1
)
echo OK - Conda detecte

echo.
echo [2/6] Suppression de l'environnement existant (si present)...
call conda env remove -n automatisation -y >nul 2>&1
echo OK

echo.
echo [3/6] Creation de l'environnement conda avec Python 3.12...
call conda create -n automatisation python=3.12 -y
if %errorlevel% neq 0 (
    echo ERREUR: Echec de creation de l'environnement
    pause
    exit /b 1
)
echo OK

echo.
echo [4/6] Activation de l'environnement...
call conda activate automatisation
if %errorlevel% neq 0 (
    echo ERREUR: Impossible d'activer l'environnement
    pause
    exit /b 1
)
echo OK

echo.
echo [5/6] Installation de PyTorch (CPU)...
echo Cette etape peut prendre plusieurs minutes...
call pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
if %errorlevel% neq 0 (
    echo ERREUR: Echec de l'installation de PyTorch
    pause
    exit /b 1
)
echo OK

echo.
echo [6/6] Installation des dependances du projet...
echo Cette etape peut prendre plusieurs minutes...

REM Installation des dependances principales
echo   - mss (capture d'ecran)...
call pip install "mss>=9.0.0"

echo   - opencv-python (vision par ordinateur)...
call pip install "opencv-python>=4.8.0"

echo   - Pillow (traitement d'images)...
call pip install "Pillow>=10.0.0"

echo   - numpy (calculs numeriques)...
call pip install "numpy>=1.24.0"

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
echo Tests         : pytest + pytest-cov
echo.
echo Pour utiliser cet environnement :
echo   1. Ouvrez un nouveau terminal Anaconda Prompt
echo   2. Tapez : conda activate automatisation
echo   3. Lancez : python main.py
echo.
echo Pour lancer les tests :
echo   pytest
echo   pytest --cov=manoirs --cov-report=term-missing
echo.
echo ========================================================================
pause
