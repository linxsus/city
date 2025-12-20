# Framework Automatisation - Documentation API

## Vue d'ensemble

Le framework fournit le moteur d'exécution et les outils pour automatiser des fenêtres.
L'application (fenetres, actions) implémente la logique métier.

```
┌─────────────────────────────────────────────────────────────┐
│                      APPLICATION                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Fenêtres   │  │   Actions   │  │  Logique métier     │ │
│  │ (instances) │  │ (concrètes) │  │                     │ │
│  └──────┬──────┘  └──────┬──────┘  └─────────────────────┘ │
└─────────┼────────────────┼──────────────────────────────────┘
          │                │
          ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                       FRAMEWORK                             │
│  ┌─────────┐  ┌───────────┐  ┌────────┐  ┌───────────────┐ │
│  │ Engine  │  │ Scheduler │  │ Vision │  │    Utils      │ │
│  └─────────┘  └───────────┘  └────────┘  └───────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. Engine (core/engine.py)

### Point d'entrée principal

```python
from core.engine import get_engine, EtatEngine

engine = get_engine()
```

### Méthodes publiques

| Méthode | Description |
|---------|-------------|
| `ajouter_fenetre(fenetre)` | Ajoute une fenêtre au moteur |
| `ajouter_fenetres(fenetres)` | Ajoute plusieurs fenêtres (dict ou list) |
| `demarrer()` | Démarre la boucle principale (bloquant) |
| `arreter()` | Demande l'arrêt propre |
| `pause()` | Met en pause |
| `reprendre()` | Reprend après pause |
| `toggle_pause()` | Bascule pause/reprise |
| `get_stats()` | Retourne les statistiques |
| `get_status()` | Retourne le statut actuel |

### Callbacks disponibles

```python
engine.set_callback('fenetre_change', callback)    # (fenetre_id, fenetre)
engine.set_callback('action_executed', callback)   # (fenetre_id, nb_actions)
engine.set_callback('error', callback)             # (fenetre_id, message)
engine.set_callback('state_change', callback)      # (ancien_etat, nouvel_etat)
```

### États du moteur (EtatEngine)

- `ARRETE` : Moteur arrêté
- `EN_COURS` : En cours d'exécution
- `EN_PAUSE` : En pause manuelle
- `ATTENTE_UTILISATEUR` : Pause car utilisateur actif
- `ARRET_EN_COURS` : Arrêt en cours

### Cycle d'exécution

```
1. Scheduler sélectionne la fenêtre (get_prochain_passage_*)
2. Si fenêtre prête :
   a. Engine appelle fenetre.preparer_tour()
   b. Engine exécute fenetre.sequence
   c. Pour chaque action : action.condition() puis action.execute()
   d. Vérifie fenetre.doit_tourner() après chaque action
3. Pause entre fenêtres
4. Retour à 1
```

---

## 2. Contrat de la Fenêtre

### Attributs requis

| Attribut | Type | Description |
|----------|------|-------------|
| `fenetre_id` | str | Identifiant unique |
| `nom` | str | Nom affichable |
| `priorite` | int | Priorité statique (0-100, plus haut = prioritaire) |
| `sequence` | SequenceActions | Séquence d'actions à exécuter |
| `slots_prioritaires` | list | Liste de slots prioritaires |
| `slots_normaux` | list | Liste de slots normaux |

### Méthodes à implémenter

```python
def get_prochain_passage_prioritaire(self) -> float:
    """Retourne dans combien de secondes traiter les actions prioritaires
    
    Returns:
        <= 0 : prête maintenant
        > 0  : revenir dans X secondes
        float('inf') : pas d'action prioritaire
    """

def get_prochain_passage_normal(self) -> float:
    """Retourne dans combien de secondes traiter les actions normales
    
    Returns:
        <= 0 : prête maintenant
        > 0  : revenir dans X secondes
        float('inf') : pas d'action normale
    """

def preparer_tour(self) -> bool:
    """Prépare le tour et alimente self.sequence
    
    Appelé par Engine avant d'exécuter les actions.
    Doit alimenter self.sequence avec les actions à exécuter.
    
    Returns:
        True si prêt à exécuter, False sinon
    """
```

### Méthodes optionnelles (surchargeables)

```python
def signaler_blocage(self):
    """Appelé quand trop d'échecs consécutifs"""

def initialiser_sequence(self):
    """Appelée une fois au démarrage"""

def doit_tourner(self) -> bool:
    """Vérifié après chaque action pour demander rotation"""

def demander_rotation(self):
    """Appelé par une action pour demander la rotation"""
```

### Méthodes utilitaires héritées (si FenetreBase)

```python
# Statistiques
def incrementer_stat(self, nom_stat, valeur=1)
def get_stats(self) -> dict
```

---

## 3. Contrat de l'Action

### Interface minimale

```python
class Action:
    def condition(self) -> bool:
        """Retourne True si l'action peut s'exécuter"""
        return True
    
    def execute(self) -> bool:
        """Exécute l'action
        
        Returns:
            True si succès, False si échec
        """
        pass
```

### Attributs optionnels

| Attribut | Type | Description |
|----------|------|-------------|
| `nom` | str | Nom de l'action (pour les logs) |

---

## 4. SimpleScheduler (core/simple_scheduler.py)

### Fonctionnement

Le scheduler interroge chaque fenêtre via :
- `get_prochain_passage_prioritaire()`
- `get_prochain_passage_normal()`

**Logique de sélection :**
1. Si une fenêtre a une action **prioritaire prête** (temps <= 0) → sélectionnée
2. Sinon → sélectionne la fenêtre avec le plus petit temps (prioritaire ou normal)
3. En cas d'égalité → priorité statique décroissante

### Utilisation directe (optionnel)

```python
from core.simple_scheduler import get_simple_scheduler

scheduler = get_simple_scheduler()

# Sélectionner une fenêtre
selection = scheduler.selectionner_fenetre(fenetres_dict)
# selection.fenetre_id, selection.prete, selection.est_prioritaire

# Temps d'attente
temps = scheduler.get_temps_attente(fenetres_dict)

# Classement complet
classement = scheduler.get_classement(fenetres_dict)
# classement['prioritaire'], classement['normal']
```

---

## 5. MessageBus (core/message_bus.py)

### Communication inter-fenêtres

```python
from core.message_bus import get_message_bus, MessageType

bus = get_message_bus()

# Envoyer un message direct
bus.send_to(source_id, destination_id, MessageType.DEMANDE_RAID, contenu)

# Broadcast à toutes les fenêtres
bus.broadcast(source_id, MessageType.KILLS_TERMINES, {'nb_kills': 10})

# Récupérer les messages
messages = bus.get_messages(fenetre_id)  # Marque comme lus
messages = bus.peek_messages(fenetre_id)  # Sans marquer

# Vérifier si messages en attente
if bus.has_messages(fenetre_id, MessageType.DEMANDE_RAID):
    ...

# Compter
nb = bus.count_messages(fenetre_id)
```

### Types de messages (MessageType)

- `DEMANDE_RAID`, `CONFIRMATION_RAID`, `ANNULATION_RAID`
- `PRIORITE_HAUTE`, `CEDE_PRIORITE`
- `TACHE_TERMINEE`, `TACHE_ECHOUEE`
- `FENETRE_PRETE`, `FENETRE_OCCUPEE`
- `KILLS_TERMINES`, `DEMANDE_AIDE_KILLS`
- `INFO`, `COMMANDE`

---

## 6. Vision (vision/)

### ScreenCapture

```python
from vision.screen_capture import get_screen_capture

screen = get_screen_capture()
image = screen.capture_window_region(rect)  # (left, top, right, bottom)
screen.save_capture(image, filepath)
```

### ImageMatcher

```python
from vision.image_matcher import get_image_matcher

matcher = get_image_matcher()

# Détecter une image
found, position, confidence = matcher.find_template(image, template_path, threshold=0.8)

# Trouver toutes les occurrences
positions = matcher.find_all_templates(image, template_path, threshold=0.8)
```

### ColorDetector

```python
from vision.color_detector import get_color_detector

detector = get_color_detector()

# Détecter une couleur
found = detector.detect_color(image, color_rgb, tolerance=10, region=None)

# Trouver la position d'une couleur
position = detector.find_color(image, color_rgb, tolerance=10)
```

### OCREngine

```python
from vision.ocr_engine import get_ocr_engine

ocr = get_ocr_engine()

# Extraire le texte
text = ocr.extract_text(image, region=None)

# Trouver un texte
position = ocr.find_text(image, search_text, region=None)
```

---

## 7. Utils

### Logger (utils/logger.py)

```python
from utils.logger import get_module_logger, get_fenetre_logger, setup_logging

# Logger pour un module
logger = get_module_logger("MonModule")
logger.info("Message")
logger.debug("Debug")
logger.error("Erreur")

# Logger pour une fenêtre (fichier séparé)
logger = get_fenetre_logger("fenetre_id")
```

### Config (utils/config.py)

```python
from utils.config import (
    PAUSE_ENTRE_ACTIONS,      # Pause entre chaque action
    PAUSE_ENTRE_FENETRES,     # Pause entre fenêtres
    TEMPS_INACTIVITE_REQUIS,  # Secondes d'inactivité avant reprise
    TEMPLATES_DIR,            # Dossier des templates
    CAPTURES_DIR,             # Dossier des captures
    DATA_DIR,                 # Dossier des données
)
```

### Coordinates (utils/coordinates.py)

```python
from utils.coordinates import relative_to_absolute, clamp_to_window

# Convertir coordonnées relatives (0-1) en absolues
abs_x, abs_y = relative_to_absolute(rel_x, rel_y, window_rect)

# Limiter aux bornes de la fenêtre
x, y = clamp_to_window(x, y, window_rect)
```

---

## 8. Autres composants (disponibles mais optionnels)

### WindowManager (core/window_manager.py)

Gestion des fenêtres Windows (trouver, activer, etc.)

```python
from core.window_manager import get_window_manager

wm = get_window_manager()
hwnd = wm.find_window("Titre fenêtre")
wm.activate_window(hwnd)
rect = wm.get_window_rect(hwnd)
```

### UserActivityDetector (core/user_activity_detector.py)

Détection souris/clavier (utilisé par Engine automatiquement)

```python
from core.user_activity_detector import get_activity_detector

activity = get_activity_detector()
if activity.is_user_active(timeout=2.0):
    ...
```

### SlotManager, TimerManager, WindowStateManager

Disponibles pour usage dans les fenêtres si besoin de persistance ou gestion avancée.

---

## 9. Structure des Slots (pour fenêtre)

```python
slot = {
    'nom': 'mercenaire',
    'prochain_disponible': timestamp,  # time.time() + delai
    'actions': [action1, action2, ...],  # Actions à exécuter
    'intervalle': 300,  # ou callable
}

# Exemple d'implémentation get_prochain_passage_prioritaire
def get_prochain_passage_prioritaire(self):
    if not self.slots_prioritaires:
        return float('inf')
    
    # Trier par timestamp
    self.slots_prioritaires.sort(key=lambda s: s['prochain_disponible'])
    
    prochain = self.slots_prioritaires[0]['prochain_disponible']
    return prochain - time.time()
```

---

## 10. Exemple d'utilisation minimal

```python
from core.engine import get_engine

# Créer une fenêtre (doit implémenter le contrat)
class MaFenetre:
    def __init__(self):
        self.fenetre_id = "ma_fenetre"
        self.nom = "Ma Fenêtre"
        self.priorite = 50
        self.sequence = SequenceActions()
        self.slots_prioritaires = []
        self.slots_normaux = []
    
    def get_prochain_passage_prioritaire(self):
        return float('inf')  # Pas d'action prioritaire
    
    def get_prochain_passage_normal(self):
        return 0  # Toujours prête
    
    def preparer_tour(self):
        self.sequence.clear()
        self.sequence.ajouter(MonAction())
        return True
    
    def doit_tourner(self):
        return False
    
    def signaler_blocage(self):
        pass
    
    def incrementer_stat(self, nom, val=1):
        pass
    
    def get_stats(self):
        return {}

# Démarrer
engine = get_engine()
engine.ajouter_fenetre(MaFenetre())
engine.demarrer()
```
