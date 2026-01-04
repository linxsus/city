@echo off
REM ============================================================================
REM Script d'installation - Environnement Intel Arc / Core Ultra
REM Framework d'automatisation Mafia City
REM ============================================================================

echo.
echo ========================================================================
echo   Installation de l'environnement AUTOMATISATION (Intel Arc / XPU)
echo ========================================================================
echo.
echo Ce script va :
echo   - Creer un environnement conda nomme "automatisation"
echo   - Installer Python 3.11 (requis pour Intel Extension for PyTorch)
echo   - Installer PyTorch avec support Intel XPU (Arc GPU)
echo   - Installer toutes les dependances (OpenCV, EasyOCR, etc.)
echo.
echo PREREQUIS:
echo   - Intel Arc GPU (A380, A580, A750, A770) ou Intel Core Ultra avec iGPU
echo   - Pilotes Intel Arc a jour (version 31.0.101.5186 ou superieure)
echo   - Intel oneAPI Base Toolkit (optionnel mais recommande)
echo.
echo Appuyez sur une touche pour continuer ou CTRL+C pour annuler...
pause >nul

echo.
echo [1/7] Verification de conda...
where conda >nul 2>&1
if %errorlevel% neq 0 (
    echo ERREUR: Conda n'est pas installe ou n'est pas dans le PATH
    echo Veuillez installer Anaconda ou Miniconda depuis https://www.anaconda.com/
    pause
    exit /b 1
)
echo OK - Conda detecte

echo.
echo [2/7] Suppression de l'environnement existant (si present)...
call conda env remove -n automatisation -y >nul 2>&1
echo OK

echo.
echo [3/7] Creation de l'environnement conda avec Python 3.11...
echo (Python 3.11 est requis pour Intel Extension for PyTorch)
call conda create -n automatisation python=3.11 -y
if %errorlevel% neq 0 (
    echo ERREUR: Echec de creation de l'environnement
    pause
    exit /b 1
)
echo OK

echo.
echo [4/7] Activation de l'environnement...
call conda activate automatisation
if %errorlevel% neq 0 (
    echo ERREUR: Impossible d'activer l'environnement
    pause
    exit /b 1
)
echo OK

echo.
echo [5/7] Installation de PyTorch avec Intel Extension for PyTorch (XPU)...
echo Cette etape peut prendre plusieurs minutes (telechargement ~2 GB)...
echo.

REM Installation de PyTorch base
call pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

REM Installation de Intel Extension for PyTorch pour XPU
echo.
echo Installation de Intel Extension for PyTorch (IPEX)...
call pip install intel-extension-for-pytorch oneccl_bind_pt --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/xpu/us/

if %errorlevel% neq 0 (
    echo.
    echo AVERTISSEMENT: L'installation Intel XPU a echoue.
    echo Le systeme fonctionnera en mode CPU.
    echo Pour le support XPU, verifiez que vos pilotes Intel sont a jour.
    echo.
)
echo OK

echo.
echo [6/7] Installation des dependances du projet...
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

echo   - EasyOCR (reconnaissance de texte)...
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
echo [7/7] Verification de l'installation Intel XPU...
python -c "import torch; import intel_extension_for_pytorch as ipex; print(f'Intel XPU disponible: {ipex.xpu.is_available()}'); print(f'Nombre de GPU Intel: {ipex.xpu.device_count()}')" 2>nul
if %errorlevel% neq 0 (
    echo.
    echo Note: Intel XPU non detecte. Le systeme utilisera le CPU.
    echo Pour activer le GPU Intel Arc, assurez-vous que :
    echo   1. Les pilotes Intel Arc sont a jour
    echo   2. Intel oneAPI Base Toolkit est installe (optionnel)
    echo.
)

echo.
echo ========================================================================
echo   INSTALLATION TERMINEE !
echo ========================================================================
echo.
echo Environnement : automatisation (Intel Arc / XPU)
echo Python        : 3.11
echo PyTorch       : Avec Intel Extension for PyTorch
echo OCR           : EasyOCR
echo Tests         : pytest + pytest-cov
echo.
echo Pour utiliser cet environnement :
echo   1. Ouvrez un nouveau terminal Anaconda Prompt
echo   2. Tapez : conda activate automatisation
echo   3. Lancez : python main.py
echo.
echo Pour verifier le support Intel XPU :
echo   python -c "import intel_extension_for_pytorch as ipex; print(ipex.xpu.is_available())"
echo.
echo ========================================================================
pause
