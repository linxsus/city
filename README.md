# Automation Framework - Mafia City

Framework d'automatisation multi-instances pour Mafia City sur BlueStacks.

## Fonctionnalités

- **Multi-instances**: Gestion simultanée de plusieurs comptes BlueStacks
- **Rotation intelligente**: Priorisation dynamique des fenêtres selon les besoins
- **Vision par ordinateur**: Détection d'images, OCR, détection de couleurs
- **Gestion des erreurs**: Détection et correction automatique des popups
- **Récupération**: Relance automatique des instances BlueStacks
- **Persistance**: Sauvegarde de l'état entre les sessions
- **Détection utilisateur**: Pause automatique si activité détectée

## Prérequis

### Windows
- Windows 10/11
- BlueStacks 5 (instances configurées avec noms uniques)
- Python 3.10+ (recommandé: 3.12)

### Python
```bash
# Environnement conda recommandé
conda create -n automatisation python=3.12
conda activate automatisation

# Dépendances principales
pip install mss opencv-python pillow numpy pyautogui pywin32 pynput

# OCR (choisir une option)
pip install easyocr          # Recommandé (GPU supporté)
# OU installer Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
```

## Installation

1. Extraire l'archive dans `C:\Projets\automation_framework\`
2. Installer les dépendances Python
3. Configurer les fenêtres dans `fenetres/config_fenetres.py`
4. Ajouter les templates d'images dans `templates/`
5. Tester avec `python main.py --test`

## Utilisation

### Démarrage simple
```bash
python main.py
```

### Options
```bash
python main.py --list              # Lister les fenêtres configurées
python main.py --status            # Afficher le statut actuel
python main.py --fenetres farm1,farm2  # Seulement certaines fenêtres
python main.py --dry-run           # Mode simulation
python main.py --verbose           # Mode debug
python main.py --test              # Lancer les tests
```

### Arrêt propre
Appuyez sur `Ctrl+C` pour un arrêt propre avec sauvegarde de l'état.

## Configuration

### fenetres/config_fenetres.py

```python
FENETRES_CONFIG = {
    "principal": {
        "nom": "Compte Principal",
        "titre_bluestacks": "BlueStacks App Player",
        "type": "principal",
        "niveau_manoir": 30,
        "priorite": 100,
    },
    "farm1": {
        "nom": "Farm 1",
        "titre_bluestacks": "BlueStacks App Player 1",
        "type": "farm",
        "rang": 1,
        "niveau_manoir": 20,
        "priorite": 50,
    },
    # Ajouter d'autres farms...
}
```

### utils/config.py

Paramètres globaux:
- Chemins des dossiers
- Timeouts et délais
- Configuration OCR
- Seuils de détection

## Structure du projet

```
automation_framework/
├── main.py                 # Point d'entrée
├── README.md               # Ce fichier
│
├── utils/                  # Utilitaires
│   ├── config.py           # Configuration globale
│   ├── logger.py           # Système de logging
│   └── coordinates.py      # Gestion des coordonnées
│
├── actions/                # Système d'actions
│   ├── item.py             # Classe de base Item
│   ├── action.py           # Actions simples
│   ├── action_if.py        # Conditions If/IfElse
│   ├── action_loops.py     # Boucles For/While
│   ├── action_switch.py    # Switch/Case
│   ├── action_longue.py    # Actions interruptibles
│   ├── actions_communes.py # Actions utilitaires
│   └── sequence_actions.py # Gestion des séquences
│
├── vision/                 # Détection visuelle
│   ├── screen_capture.py   # Capture d'écran
│   ├── image_matcher.py    # Template matching
│   ├── color_detector.py   # Détection de couleurs
│   └── ocr_engine.py       # Reconnaissance de texte
│
├── core/                   # Composants principaux
│   ├── engine.py           # Moteur principal
│   ├── priority_scheduler.py # Ordonnancement
│   ├── window_manager.py   # Gestion fenêtres Windows
│   ├── window_state_manager.py # État des fenêtres
│   ├── timer_manager.py    # Gestion des timers
│   ├── slot_manager.py     # Gestion des slots
│   ├── message_bus.py      # Communication inter-fenêtres
│   ├── recovery_manager.py # Récupération d'erreurs
│   └── user_activity_detector.py # Détection utilisateur
│
├── erreurs/                # Gestion des erreurs
│   ├── item_erreur.py      # Classe ItemErreur
│   └── liste_erreurs.py    # Catalogue d'erreurs Mafia City
│
├── fenetres/               # Gestion des fenêtres
│   ├── fenetre_base.py     # Classe abstraite de base
│   ├── fenetre_farm_base.py # Base pour les farms
│   ├── config_fenetres.py  # Configuration
│   └── instances/          # Classes concrètes
│       ├── fenetre_principal.py
│       └── fenetre_farm.py
│
├── templates/              # Images de référence
│   ├── popups/             # Popups d'erreur
│   ├── boutons/            # Boutons cliquables
│   ├── ville/              # Éléments ville
│   ├── carte/              # Éléments carte
│   ├── mercenaires/        # Mercenaires
│   └── evenements/         # Événements
│
├── data/                   # Données persistées (auto-créé)
│   ├── timers.json
│   ├── slots.json
│   └── window_states.json
│
├── logs/                   # Logs (auto-créé)
│   ├── automation.log
│   └── captures/           # Screenshots de debug
│
└── tests/                  # Tests unitaires
    ├── test_phase1.py      # Utils
    ├── test_phase2.py      # Actions
    ├── test_phase3.py      # Vision
    ├── test_phase4.py      # Window manager
    ├── test_phase5.py      # Persistance
    ├── test_phase6.py      # Erreurs
    ├── test_phase7.py      # Scheduler
    ├── test_phase8.py      # Fenêtres
    └── test_phase9.py      # Engine
```

## Architecture

### Flux d'exécution

```
main.py
    │
    ▼
Engine (core/engine.py)
    │
    ├─► PriorityScheduler ──► Sélection fenêtre
    │
    ├─► UserActivityDetector ──► Pause si utilisateur actif
    │
    ├─► FenetreBase ──► Exécution des actions
    │       │
    │       ├─► SequenceActions ──► File d'actions
    │       │
    │       ├─► Vision (capture, matching, OCR)
    │       │
    │       └─► Interactions (clics, saisie)
    │
    ├─► RecoveryManager ──► Récupération d'erreurs
    │
    └─► Persistance (Timers, Slots, États)
```

### Système de priorités

Le scheduler calcule un score pour chaque fenêtre:

| Composante | Poids | Description |
|------------|-------|-------------|
| Priorité statique | ×1.0 | Configuration |
| Slots disponibles | +20/slot | Slots libres |
| Timer dû | +50/timer | Actions planifiées |
| Timer urgent (>5min) | +100 | Retard important |
| Message prioritaire | +80 | Communication urgente |
| Kill Event | +200 | Événement spécial |

## Personnalisation

### Ajouter une nouvelle action

```python
from actions.action import Action

class MonAction(Action):
    def __init__(self, fenetre, param):
        super().__init__(fenetre)
        self.param = param
    
    def _run(self):
        # Logique de l'action
        self.fenetre.click_image("mon_bouton.png")
        return True
```

### Ajouter une nouvelle erreur

```python
from erreurs.item_erreur import ItemErreurImage

erreur = ItemErreurImage(
    fenetre=fenetre,
    image="templates/popups/mon_erreur.png",
    message="Mon erreur détectée",
    action_correction=action_clic_ok,
    exclure_fenetre=60,  # Exclure 60 secondes
)
```

### Créer un nouveau type de fenêtre

```python
from fenetres.fenetre_base import FenetreBase

class MaFenetre(FenetreBase):
    def initialiser_sequence(self):
        # Initialiser la séquence d'actions
        pass
    
    def definir_timers(self):
        # Définir les timers
        self._tm.add_timer("ma_tache", self.fenetre_id, 3600)
    
    def construire_sequence_selon_timers(self):
        # Construire la séquence selon les timers dus
        pass
```

## Dépannage

### BlueStacks non détecté
- Vérifiez que le titre de la fenêtre correspond exactement à `titre_bluestacks`
- Lancez en mode admin si nécessaire

### Templates non détectés
- Vérifiez que le template est bien découpé
- Essayez de baisser le seuil (0.7 au lieu de 0.8)
- Assurez-vous que la résolution est identique

### OCR ne fonctionne pas
- Installez Tesseract et configurez `TESSERACT_CMD` dans config.py
- Ou installez EasyOCR: `pip install easyocr`

### Erreur pywin32
- Réinstallez: `pip install --upgrade pywin32`
- Exécutez: `python Scripts/pywin32_postinstall.py -install`

## Licence

Usage personnel uniquement. Non affilié à Mafia City ou YottaGames.

## Changelog

### v1.0.0 (Phase 10)
- Version initiale complète
- Support multi-instances BlueStacks
- Système d'actions modulaire
- Vision par ordinateur (OpenCV, OCR)
- Gestion des erreurs automatique
- Persistance de l'état
- Détection d'activité utilisateur
