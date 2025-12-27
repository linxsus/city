# CLAUDE.md - Guide du projet

## Apercu du projet

Ce projet est un **framework d'automatisation multi-instances** pour le jeu mobile Mafia City, concu pour fonctionner avec BlueStacks. Il comprend deux composantes principales:

1. **Framework d'automatisation** (existant) - Moteur d'execution pour automatiser des fenetres de jeu
2. **Generateur de classes** (a developper) - Outil web pour creer les elements d'automatisation

## Structure du projet

```
city/
├── main.py                 # Point d'entree principal
├── maintest.py             # Tests du framework
├── config/                 # Configuration globale
├── core/                   # Composants principaux du framework
│   ├── engine.py           # Moteur principal
│   ├── etat.py             # Classe de base Etat
│   └── ...
├── actions/                # Systeme d'actions
│   ├── action.py           # Actions simples
│   ├── action_longue.py    # Actions interruptibles
│   └── ...
├── vision/                 # Detection visuelle (OpenCV, OCR)
├── erreurs/                # Gestion des erreurs
├── manoirs/                # Configuration des instances
├── templates/              # Images de reference pour detection
├── data/                   # Donnees persistees
├── logs/                   # Fichiers de log
├── tests/                  # Tests unitaires
├── docs/                   # Documentation technique
│   ├── cahier_des_charges_generateur.md
│   └── specifications_techniques_generateur.md
└── utils/                  # Utilitaires
```

## Concepts cles

### Etats (Etat)
Un **Etat** represente un ecran ou une situation dans le jeu. Chaque etat:
- A un nom unique et appartient a des groupes
- Possede une methode `verif()` pour detecter s'il est actif (via image ou OCR)
- A une priorite (les popups ont une priorite elevee 80-100)

```python
class EtatVille(Etat):
    nom = "ville"
    groupes = ["ecran_principal"]

    def verif(self, manoir) -> bool:
        return manoir.detect_image("ville/icone.png")
```

### Chemins (Chemin)
Un **Chemin** definit la transition entre deux etats via une sequence d'actions:
- Etat initial et etat de sortie
- Liste d'actions a executer
- Gestion des etats de sortie incertains (popups, erreurs)

```python
class CheminLancerJeu(Chemin):
    etat_initial = "non_lance"
    etat_sortie = "chargement"

    def fonction_actions(self, manoir) -> List[Any]:
        return [
            ActionBouton(manoir, "bouton_lancer.png"),
            ActionAttendre(manoir, 5),
        ]
```

### Actions
Types d'actions disponibles:
- **ActionBouton**: Clic sur une image/template
- **ActionAttendre**: Delai/pause
- **ActionTexte**: Clic sur un texte detecte par OCR
- **ActionLongue**: Action interruptible de longue duree avec structures de controle

### Slots et Timers
- **Slots**: Representent des ressources limitees (ex: file de construction)
- **Timers**: Planifient des actions futures

## Generateur de classes (a developper)

### Objectif
Creer une interface web permettant de generer automatiquement les classes Etat, Chemin, Action et ActionLongue a partir d'images, avec assistance IA (Claude).

### Stack technique
| Composant | Technologie |
|-----------|-------------|
| Backend | FastAPI |
| Frontend | HTML/CSS/JavaScript + Blockly |
| IA | API Claude (Anthropic) |
| Traitement image | OpenCV, Pillow |
| OCR | pytesseract ou EasyOCR |
| Templates | Jinja2 |

### Fonctionnalites IA
- Suggestion de zones caracteristiques pour detection
- Detection de texte OCR
- Suggestion de groupes et priorites
- Detection de zones cliquables
- Suggestion de seuils de detection optimaux

### Architecture cible

```
generateur/
├── main.py                      # Point d'entree FastAPI
├── config.py                    # Configuration
├── api/routes/                  # Endpoints REST
├── services/                    # Logique metier
│   ├── claude_service.py        # Integration Claude
│   ├── etat_service.py
│   └── ...
├── generators/                  # Generation de code
│   ├── etat_generator.py
│   └── templates/*.j2
├── models/schemas.py            # Schemas Pydantic
├── blockly/                     # Integration Blockly
└── static/                      # Frontend
```

### Phases de developpement

**Phase 1 - MVP**
1. Interface web basique
2. Creation d'etats simples (image OU texte)
3. Creation de chemins simples
4. Generation du code Python
5. Integration API Claude basique

**Phase 2 - Fonctionnalites avancees**
1. ActionLongue avec blocs visuels (Blockly)
2. Structures de controle (if, loop)
3. Gestion des erreurs complete

**Phase 3 - Import et synchronisation**
1. Import des elements existants
2. Synchronisation bidirectionnelle

## API du framework existant

### Engine (core/engine.py)
```python
from core.engine import get_engine

engine = get_engine()
engine.ajouter_fenetre(fenetre)
engine.demarrer()  # Bloquant
```

### Vision
```python
from vision.image_matcher import get_image_matcher
from vision.ocr_engine import get_ocr_engine

# Detection d'image
matcher = get_image_matcher()
found, position, confidence = matcher.find_template(image, template_path, threshold=0.8)

# OCR
ocr = get_ocr_engine()
text = ocr.extract_text(image, region=None)
```

### MessageBus
```python
from core.message_bus import get_message_bus, MessageType

bus = get_message_bus()
bus.send_to(source_id, dest_id, MessageType.DEMANDE_RAID, contenu)
bus.broadcast(source_id, MessageType.INFO, data)
```

## Conventions de code

### Nommage
- Classes: PascalCase (ex: `EtatVille`, `CheminLancerJeu`)
- Fichiers: snake_case (ex: `etat_ville.py`, `chemin_lancer_jeu.py`)
- Variables: snake_case
- Constantes: UPPER_SNAKE_CASE

### Structure d'un Etat genere
```python
from core.etat import Etat

class EtatNomEtat(Etat):
    nom = "nom_etat"
    groupes = ["groupe1", "groupe2"]
    priorite = 0  # 0 normal, 80-100 pour popups

    def verif(self, manoir) -> bool:
        return manoir.detect_image("template.png", threshold=0.8)
```

### Seuils de detection
- Valeur par defaut: 0.8
- Plage valide: 0.5 - 1.0
- Popups: souvent 0.85+

## Commandes utiles

```bash
# Lancer le framework
python main.py

# Lancer les tests
python main.py --test

# Mode simulation
python main.py --dry-run

# Mode verbose
python main.py --verbose
```

## Environnement de developpement

```bash
# Creation environnement conda
conda create -n automatisation python=3.12
conda activate automatisation

# Installation dependances
pip install -r requirements.txt

# Dependances principales
# mss opencv-python pillow numpy pyautogui pywin32 pynput easyocr
```

## Documentation supplementaire

- `docs/cahier_des_charges_generateur.md` - Specifications fonctionnelles du generateur
- `docs/specifications_techniques_generateur.md` - Specifications techniques detaillees
- `API.md` - Documentation API complete du framework
- `INSTALLATION.md` - Guide d'installation detaille
