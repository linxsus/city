# Guide d'installation - Framework Automatisation Mafia City

## 📋 Prérequis

### Windows
- **Windows 10/11** (64-bit)
- **BlueStacks 5** installé et configuré
- **Anaconda** ou **Miniconda** installé ([télécharger ici](https://www.anaconda.com/download))

### Pour la version GPU NVIDIA (optionnel)
- **Carte graphique NVIDIA** compatible CUDA
- **CUDA 12.1** installé ([télécharger ici](https://developer.nvidia.com/cuda-downloads))
- **Pilotes NVIDIA** à jour

### Pour la version GPU Intel Arc (optionnel)
- **Intel Arc** (A380, A580, A750, A770) ou **Intel Core Ultra** avec iGPU
- **Pilotes Intel Arc** à jour (version 31.0.101.5186 ou supérieure)
- Télécharger les pilotes : [Intel Arc Graphics](https://www.intel.com/content/www/us/en/download/726609/intel-arc-iris-xe-graphics-whql-windows.html)

---

## 🚀 Installation automatique

Nous avons créé des scripts batch pour automatiser complètement l'installation.

### Option 1 : CPU uniquement (recommandé pour débuter)

1. Double-cliquez sur `setup_env_cpu.bat`
2. Suivez les instructions à l'écran
3. Attendez la fin de l'installation (~5-10 minutes)

✅ **Avantages** : Plus rapide, moins d'espace disque, fonctionne sur tous les PC
❌ **Inconvénient** : OCR plus lent (acceptable pour la plupart des usages)

### Option 2 : GPU NVIDIA avec CUDA 12.1

**Prérequis** : CUDA 12.1 doit être installé

1. Double-cliquez sur `setup_env_gpu.bat`
2. Suivez les instructions à l'écran
3. Attendez la fin de l'installation (~10-15 minutes, téléchargement ~3 GB)

✅ **Avantages** : OCR beaucoup plus rapide avec EasyOCR
❌ **Inconvénient** : Nécessite GPU NVIDIA + CUDA

### Option 3 : Intel optimisé + scrcpy (recommandé pour Android)

**Pour** : Processeurs Intel (Core Ultra, etc.) + automatisation via téléphone Android

1. Double-cliquez sur `setup_env_intel.bat`
2. Suivez les instructions à l'écran
3. Attendez la fin de l'installation (~10-15 minutes)
4. **Rouvrez Anaconda Prompt** après installation (pour le PATH scrcpy/adb)

✅ **Avantages** : Installe scrcpy/ADB automatiquement, Intel MKL pour bonnes performances CPU
❌ **Inconvénient** : Nécessite winget (Windows 10/11)

**Inclus** : scrcpy, ADB, PyTorch avec Intel MKL

---

## 🎮 Utilisation

### Méthode 1 : Script de lancement rapide

Double-cliquez sur `run.bat` - C'est tout ! 🎉

### Méthode 2 : Ligne de commande

```bash
# Ouvrir "Anaconda Prompt"
conda activate automatisation
python main.py
```

### Options de lancement

```bash
# Lister les manoirs configurés
python main.py --list

# Lancer seulement certains manoirs
python main.py --manoirs farm1,farm2

# Mode simulation (pas d'actions réelles)
python main.py --dry-run

# Mode verbose (debug)
python main.py --verbose

# Afficher le statut
python main.py --status
```

---

## 🔧 Détails de l'installation

### Ce qui est installé

| Package | Version | Usage |
|---------|---------|-------|
| Python | 3.12 | Langage de base |
| PyTorch | Latest (CPU ou CUDA 12.1) | Backend pour EasyOCR |
| EasyOCR | ≥1.7.0 | Reconnaissance de texte (OCR) |
| OpenCV | ≥4.8.0 | Vision par ordinateur |
| NumPy | ≥1.24.0 | Calculs numériques |
| Pillow | ≥10.0.0 | Traitement d'images |
| MSS | ≥9.0.0 | Capture d'écran rapide |
| PyAutoGUI | ≥0.9.54 | Automatisation clavier/souris |
| PyWin32 | ≥306 | Intégration Windows |
| Pynput | ≥1.7.6 | Détection activité utilisateur |

### Espace disque requis

- **Version CPU** : ~2 GB
- **Version GPU** : ~4 GB (PyTorch CUDA est plus lourd)

---

## ✅ Vérification de l'installation

### 1. Vérifier que l'environnement existe

```bash
conda env list
# Vous devriez voir "automatisation" dans la liste
```

### 2. Vérifier Python

```bash
conda activate automatisation
python --version
# Doit afficher : Python 3.12.x
```

### 3. Vérifier PyTorch (GPU NVIDIA)

```bash
conda activate automatisation
python -c "import torch; print(f'CUDA disponible: {torch.cuda.is_available()}')"
python -c "import torch; print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"Aucun\"}')"
```

Résultat attendu :
```
CUDA disponible: True
GPU: NVIDIA GeForce RTX 3060
```

### 3b. Vérifier PyTorch (GPU Intel Arc)

```bash
conda activate automatisation
python check_intel_xpu.py
```

Ou manuellement :
```bash
python -c "import intel_extension_for_pytorch as ipex; print(f'XPU disponible: {ipex.xpu.is_available()}')"
```

Résultat attendu :
```
XPU disponible: True
```

### 4. Tester EasyOCR

```bash
conda activate automatisation
python -c "import easyocr; print('EasyOCR OK')"
```

---

## 🐛 Dépannage

### Erreur : "conda n'est pas reconnu..."

**Solution** : Utilisez "Anaconda Prompt" au lieu de l'invite de commandes Windows classique

### Erreur lors de l'installation de PyTorch GPU

**Causes possibles** :
- CUDA 12.1 n'est pas installé → [Installer CUDA 12.1](https://developer.nvidia.com/cuda-downloads)
- Pilotes NVIDIA obsolètes → Mettre à jour via GeForce Experience
- GPU incompatible → Utiliser `setup_env_cpu.bat` à la place

### Erreur : "pywin32 failed to install"

**Solution** :
```bash
conda activate automatisation
pip install --upgrade pywin32
python Scripts/pywin32_postinstall.py -install
```

### EasyOCR très lent

**Cause** : Version CPU utilisée

**Solutions** :
- Option A : Passer à la version GPU (`setup_env_gpu.bat`)
- Option B : Utiliser Tesseract à la place (modifier `utils/config.py`)

### Conflit avec un environnement existant

**Solution** : Supprimer l'ancien et réinstaller
```bash
conda env remove -n automatisation
# Puis relancer setup_env_cpu.bat ou setup_env_gpu.bat
```

---

## 🔄 Mise à jour

Pour mettre à jour les dépendances :

```bash
conda activate automatisation
pip install --upgrade -r requirements.txt
```

---

## 📦 Désinstallation

Pour supprimer complètement l'environnement :

```bash
conda env remove -n automatisation
```

---

## 💡 Conseils

1. **Première utilisation** : Commencez avec `setup_env_cpu.bat` pour tester
2. **Performance** : Si l'OCR est trop lent, passez à la version GPU
3. **Mise à jour** : Exécutez `git pull` régulièrement pour obtenir les nouvelles fonctionnalités
4. **Sauvegarde** : Le dossier `data/` contient vos configurations, sauvegardez-le

---

## 📞 Support

En cas de problème :
1. Vérifiez cette documentation
2. Consultez le fichier `README.md` principal
3. Vérifiez les logs dans `logs/automation.log`
4. Ouvrez une issue sur GitHub avec les logs d'erreur

---

## 🎯 Prochaines étapes

Une fois l'installation terminée :

1. Configurez vos instances BlueStacks dans `manoirs/config_manoirs.py`
2. Ajoutez vos templates d'images dans `templates/`
3. Lancez avec `run.bat` ou `python main.py`
4. Consultez `API.md` pour personnaliser le comportement

Bon jeu ! 🎮
