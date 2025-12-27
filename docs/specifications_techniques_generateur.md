# Spécifications Techniques - Générateur de Classes

## 1. Architecture Générale

### 1.1 Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              NAVIGATEUR WEB                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌─────────────────┐   │
│  │   Vue État  │  │  Vue Chemin  │  │ Vue Action  │  │ Vue ActionLongue│   │
│  └──────┬──────┘  └──────┬───────┘  └──────┬──────┘  └────────┬────────┘   │
│         │                │                  │                  │            │
│  ┌──────┴──────────────┴──────────────────┴──────────────────┴────────┐   │
│  │                        Blockly Editor                               │   │
│  └──────────────────────────────┬──────────────────────────────────────┘   │
└─────────────────────────────────┼───────────────────────────────────────────┘
                                  │ WebSocket / REST API
┌─────────────────────────────────┼───────────────────────────────────────────┐
│                          BACKEND PYTHON                                      │
├─────────────────────────────────┼───────────────────────────────────────────┤
│  ┌──────────────────────────────┴───────────────────────────────────────┐   │
│  │                         API Controller                                │   │
│  │                    (FastAPI / Flask-RESTX)                           │   │
│  └───────┬───────────────┬───────────────┬────────────────┬─────────────┘   │
│          │               │               │                │                  │
│  ┌───────┴───────┐ ┌─────┴─────┐ ┌───────┴───────┐ ┌─────┴─────────┐       │
│  │ État Service  │ │ Chemin    │ │ Action        │ │ Template      │       │
│  │               │ │ Service   │ │ Service       │ │ Service       │       │
│  └───────┬───────┘ └─────┬─────┘ └───────┬───────┘ └─────┬─────────┘       │
│          │               │               │                │                  │
│  ┌───────┴───────────────┴───────────────┴────────────────┴─────────────┐   │
│  │                        Code Generator                                 │   │
│  └──────────────────────────────┬────────────────────────────────────────┘   │
│                                 │                                            │
│  ┌──────────────────────────────┴────────────────────────────────────────┐   │
│  │                         Claude AI Service                             │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────┼───────────────────────────────────────────┐
│                          SYSTÈME DE FICHIERS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌─────────────────┐   │
│  │  genere/    │  │  templates/  │  │   config/   │  │  brouillons/    │   │
│  │  (code)     │  │  (images)    │  │   (json)    │  │  (sessions)     │   │
│  └─────────────┘  └──────────────┘  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Stack Technologique

| Composant | Technologie | Version Minimale |
|-----------|-------------|------------------|
| Backend | FastAPI | 0.100+ |
| Frontend | Vanilla JS + Blockly | ES2020+ |
| IA | Claude API (Anthropic) | claude-3-opus |
| Traitement Image | OpenCV, Pillow | opencv-4.8+, Pillow-10+ |
| OCR | pytesseract | 0.3.10+ |
| Template | Jinja2 | 3.1+ |
| Configuration | TOML/JSON | tomllib (Python 3.11+) |
| Tests | pytest, pytest-asyncio | 7.0+ |

---

## 2. Modèles de Données

### 2.1 Schémas Pydantic

#### EtatSchema

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from enum import Enum

class MethodeVerification(str, Enum):
    IMAGE = "image"
    TEXTE = "texte"
    COMBINAISON = "combinaison"

class EtatSchema(BaseModel):
    """Schéma de définition d'un État"""
    nom: str = Field(..., min_length=1, max_length=50, pattern=r'^[a-z][a-z0-9_]*$')
    nom_classe: str = Field(..., description="Nom de la classe Python (ex: EtatVille)")
    groupes: List[str] = Field(default_factory=list)
    priorite: int = Field(default=0, ge=-100, le=100)

    # Vérification
    methode_verif: MethodeVerification = MethodeVerification.IMAGE
    template_path: Optional[str] = None
    template_region: Optional[RegionSchema] = None
    texte_ocr: Optional[str] = None
    texte_region: Optional[RegionSchema] = None
    threshold: float = Field(default=0.8, ge=0.5, le=1.0)

    # Métadonnées
    image_source: str = Field(..., description="Chemin de l'image source originale")
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class RegionSchema(BaseModel):
    """Région rectangulaire dans une image"""
    x: int = Field(..., ge=0)
    y: int = Field(..., ge=0)
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)
```

#### CheminSchema

```python
class CheminSchema(BaseModel):
    """Schéma de définition d'un Chemin"""
    nom: str = Field(..., min_length=1, max_length=100)
    nom_classe: str
    etat_initial: str = Field(..., description="Nom de l'état de départ")
    etat_sortie: str = Field(..., description="Nom de l'état d'arrivée principal")
    etats_sortie_possibles: List[str] = Field(
        default_factory=list,
        description="Liste des états de sortie alternatifs"
    )

    # Actions du chemin
    actions: List[ActionReference] = Field(default_factory=list)

    # Métadonnées
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class ActionReference(BaseModel):
    """Référence à une action dans un chemin"""
    type: Literal["ActionBouton", "ActionAttendre", "ActionTexte", "ActionLongue"]
    parametres: Dict[str, Any]
    ordre: int
```

#### ActionSchema

```python
class ActionBoutonSchema(BaseModel):
    """Schéma pour ActionBouton"""
    type: Literal["ActionBouton"] = "ActionBouton"
    template_path: str
    template_region: RegionSchema
    offset_x: int = Field(default=0)
    offset_y: int = Field(default=0)
    threshold: float = Field(default=0.8, ge=0.5, le=1.0)
    delai_avant: float = Field(default=0.0, ge=0.0)
    delai_apres: float = Field(default=0.1, ge=0.0)

class ActionAttendreSchema(BaseModel):
    """Schéma pour ActionAttendre"""
    type: Literal["ActionAttendre"] = "ActionAttendre"
    duree: float = Field(..., gt=0, le=300)

class ActionTexteSchema(BaseModel):
    """Schéma pour ActionTexte"""
    type: Literal["ActionTexte"] = "ActionTexte"
    texte_recherche: str
    region: Optional[RegionSchema] = None
    offset_x: int = Field(default=0)
    offset_y: int = Field(default=0)

class ActionLongueSchema(BaseModel):
    """Schéma pour ActionLongue"""
    type: Literal["ActionLongue"] = "ActionLongue"
    nom: str
    nom_classe: str
    etat_entree: str
    etat_sortie: str

    # Blocs Blockly sérialisés
    blockly_workspace: str = Field(..., description="JSON du workspace Blockly")

    # Séquence d'actions générée
    sequence_actions: List[ActionReference] = Field(default_factory=list)

    # Structures de contrôle
    structures_controle: List[StructureControle] = Field(default_factory=list)

class StructureControle(BaseModel):
    """Structure de contrôle (if, loop, switch)"""
    type: Literal["if", "loop", "switch"]
    condition: Optional[str] = None
    iterations: Optional[int] = None
    actions_bloc: List[ActionReference] = Field(default_factory=list)
```

### 2.2 Schéma Base de Données (SQLite optionnel)

```sql
-- Table des sessions de travail (brouillons)
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL CHECK(type IN ('etat', 'chemin', 'action', 'action_longue')),
    data_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des templates générés
CREATE TABLE templates (
    id TEXT PRIMARY KEY,
    nom TEXT NOT NULL UNIQUE,
    image_path TEXT NOT NULL,
    hash_image TEXT NOT NULL,
    region_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour détection de duplicatas
CREATE INDEX idx_templates_hash ON templates(hash_image);

-- Table des groupes d'états
CREATE TABLE groupes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL UNIQUE,
    description TEXT
);

-- Table des erreurs connues
CREATE TABLE erreurs (
    id TEXT PRIMARY KEY,
    nom TEXT NOT NULL UNIQUE,
    template_path TEXT,
    texte_ocr TEXT,
    priorite INTEGER DEFAULT 100
);
```

---

## 3. API REST

### 3.1 Endpoints

#### États

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/etats` | Liste tous les états |
| `GET` | `/api/etats/{nom}` | Récupère un état par nom |
| `POST` | `/api/etats` | Crée un nouvel état |
| `PUT` | `/api/etats/{nom}` | Modifie un état existant |
| `DELETE` | `/api/etats/{nom}` | Supprime un état |
| `POST` | `/api/etats/preview` | Prévisualise le code généré |

#### Chemins

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/chemins` | Liste tous les chemins |
| `GET` | `/api/chemins/{nom}` | Récupère un chemin par nom |
| `POST` | `/api/chemins` | Crée un nouveau chemin |
| `PUT` | `/api/chemins/{nom}` | Modifie un chemin existant |
| `DELETE` | `/api/chemins/{nom}` | Supprime un chemin |
| `POST` | `/api/chemins/preview` | Prévisualise le code généré |
| `POST` | `/api/chemins/simulate` | Simule l'exécution du chemin |

#### Actions

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/actions` | Liste toutes les actions |
| `POST` | `/api/actions/bouton` | Crée une ActionBouton |
| `POST` | `/api/actions/attendre` | Crée une ActionAttendre |
| `POST` | `/api/actions/texte` | Crée une ActionTexte |
| `POST` | `/api/actions/longue` | Crée une ActionLongue |

#### Images et Templates

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/images/upload` | Upload une image source |
| `POST` | `/api/images/crop` | Découpe une région d'image |
| `GET` | `/api/templates` | Liste tous les templates |
| `POST` | `/api/templates/check-duplicate` | Vérifie les duplicatas |
| `POST` | `/api/templates/test-threshold` | Teste le seuil optimal |

#### IA Claude

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/ia/suggest-region` | Suggère une région caractéristique |
| `POST` | `/api/ia/detect-text` | Détecte le texte caractéristique |
| `POST` | `/api/ia/suggest-group` | Suggère un groupe pour l'état |
| `POST` | `/api/ia/suggest-priority` | Suggère une priorité |
| `POST` | `/api/ia/detect-buttons` | Détecte les zones cliquables |
| `POST` | `/api/ia/suggest-errors` | Suggère les erreurs potentielles |

#### Sessions (Brouillons)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/sessions` | Liste les sessions actives |
| `GET` | `/api/sessions/{id}` | Récupère une session |
| `POST` | `/api/sessions` | Sauvegarde une session |
| `DELETE` | `/api/sessions/{id}` | Supprime une session |

### 3.2 Formats de Requêtes/Réponses

#### Création d'État - Request

```json
POST /api/etats
Content-Type: application/json

{
  "nom": "ville_principale",
  "groupes": ["ecran_principal", "navigation"],
  "priorite": 0,
  "methode_verif": "image",
  "image_source": "/tmp/uploads/capture_001.png",
  "template_region": {
    "x": 100,
    "y": 50,
    "width": 200,
    "height": 100
  },
  "threshold": 0.85
}
```

#### Création d'État - Response

```json
{
  "success": true,
  "data": {
    "nom": "ville_principale",
    "nom_classe": "EtatVillePrincipale",
    "fichier_genere": "genere/etats/etat_ville_principale.py",
    "template_path": "genere/templates/ville_principale/template.png"
  },
  "code_preview": "class EtatVillePrincipale(Etat):\n    nom = \"ville_principale\"\n    ..."
}
```

#### Suggestion IA - Request

```json
POST /api/ia/suggest-region
Content-Type: application/json

{
  "image_path": "/tmp/uploads/capture_001.png",
  "context": "Écran principal du jeu avec menu de navigation"
}
```

#### Suggestion IA - Response

```json
{
  "success": true,
  "suggestions": [
    {
      "region": {"x": 100, "y": 50, "width": 200, "height": 100},
      "confidence": 0.92,
      "description": "Zone d'icône caractéristique du menu principal",
      "raison": "Cette zone contient un élément unique et stable"
    },
    {
      "region": {"x": 300, "y": 20, "width": 150, "height": 80},
      "confidence": 0.85,
      "description": "Titre de la page",
      "raison": "Texte distinctif de cet écran"
    }
  ],
  "texte_detecte": ["Menu Principal", "Jouer", "Options"],
  "groupe_suggere": "ecran_principal",
  "priorite_suggeree": 0
}
```

---

## 4. Services Backend

### 4.1 Structure des Modules

```
generateur/
├── __init__.py
├── main.py                      # Point d'entrée FastAPI
├── config.py                    # Configuration globale
│
├── api/
│   ├── __init__.py
│   ├── routes/
│   │   ├── etats.py            # Routes API états
│   │   ├── chemins.py          # Routes API chemins
│   │   ├── actions.py          # Routes API actions
│   │   ├── images.py           # Routes API images
│   │   ├── ia.py               # Routes API Claude
│   │   └── sessions.py         # Routes API sessions
│   └── dependencies.py          # Dépendances FastAPI
│
├── services/
│   ├── __init__.py
│   ├── etat_service.py         # Logique métier états
│   ├── chemin_service.py       # Logique métier chemins
│   ├── action_service.py       # Logique métier actions
│   ├── template_service.py     # Gestion des templates
│   ├── claude_service.py       # Intégration API Claude
│   ├── image_service.py        # Traitement d'images
│   ├── ocr_service.py          # Service OCR
│   └── duplicate_service.py    # Détection duplicatas
│
├── generators/
│   ├── __init__.py
│   ├── base_generator.py       # Classe de base génération
│   ├── etat_generator.py       # Génération code états
│   ├── chemin_generator.py     # Génération code chemins
│   ├── action_generator.py     # Génération code actions
│   └── templates/              # Templates Jinja2
│       ├── etat.py.j2
│       ├── chemin.py.j2
│       ├── action_bouton.py.j2
│       ├── action_attendre.py.j2
│       ├── action_texte.py.j2
│       └── action_longue.py.j2
│
├── models/
│   ├── __init__.py
│   ├── schemas.py              # Schémas Pydantic
│   ├── database.py             # Modèles SQLite
│   └── enums.py                # Énumérations
│
├── blockly/
│   ├── __init__.py
│   ├── parser.py               # Parse le workspace Blockly
│   ├── blocks.py               # Définitions des blocs personnalisés
│   └── code_generator.py       # Convertit blocs → Python
│
└── utils/
    ├── __init__.py
    ├── naming.py               # Utilitaires de nommage
    ├── image_utils.py          # Utilitaires image
    └── file_utils.py           # Utilitaires fichiers
```

### 4.2 Service Claude (claude_service.py)

```python
from anthropic import Anthropic
import base64
from typing import Optional, List
from ..models.schemas import RegionSchema, SuggestionIA

class ClaudeService:
    """Service d'intégration avec l'API Claude"""

    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-opus-20240229"

    async def analyser_image(
        self,
        image_path: str,
        contexte: Optional[str] = None
    ) -> dict:
        """
        Analyse une image et suggère les zones caractéristiques.

        Args:
            image_path: Chemin vers l'image à analyser
            contexte: Description optionnelle du contexte

        Returns:
            Dict contenant les suggestions de régions, textes, groupes, priorités
        """
        image_data = self._encode_image(image_path)

        prompt = self._build_analysis_prompt(contexte)

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )

        return self._parse_response(response)

    async def detecter_boutons(self, image_path: str) -> List[RegionSchema]:
        """Détecte les zones cliquables dans une image"""
        ...

    async def suggerer_groupe(
        self,
        image_path: str,
        groupes_existants: List[str]
    ) -> str:
        """Suggère le groupe approprié pour un état"""
        ...

    async def suggerer_erreurs(
        self,
        image_path: str,
        erreurs_connues: List[dict]
    ) -> List[dict]:
        """Suggère les erreurs potentielles basées sur le contexte"""
        ...

    def _encode_image(self, image_path: str) -> str:
        """Encode une image en base64"""
        with open(image_path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode("utf-8")

    def _build_analysis_prompt(self, contexte: Optional[str]) -> str:
        """Construit le prompt d'analyse"""
        base_prompt = """Analyse cette capture d'écran d'un jeu mobile.

Identifie:
1. Une zone rectangulaire caractéristique et unique pour identifier cet écran
   - Donne les coordonnées (x, y, largeur, hauteur)
   - Explique pourquoi cette zone est distinctive

2. Le texte visible qui pourrait identifier cet écran
   - Liste les textes importants

3. Le type d'écran (menu, popup, jeu, chargement, etc.)
   - Suggère un nom de groupe approprié

4. La priorité de détection (les popups ont une haute priorité 80-100)

Réponds en JSON avec le format:
{
  "regions": [{"x": int, "y": int, "width": int, "height": int, "description": str}],
  "textes": [str],
  "type_ecran": str,
  "groupe_suggere": str,
  "priorite": int,
  "explication": str
}"""

        if contexte:
            base_prompt += f"\n\nContexte additionnel: {contexte}"

        return base_prompt
```

### 4.3 Générateur de Code (etat_generator.py)

```python
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from ..models.schemas import EtatSchema

class EtatGenerator:
    """Génère le code Python pour les classes Etat"""

    def __init__(self, templates_dir: Path):
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
        self.template = self.env.get_template("etat.py.j2")

    def generer(self, etat: EtatSchema) -> str:
        """
        Génère le code Python pour un état.

        Args:
            etat: Schéma de l'état à générer

        Returns:
            Code Python généré
        """
        return self.template.render(
            nom_classe=etat.nom_classe,
            nom=etat.nom,
            groupes=etat.groupes,
            priorite=etat.priorite,
            methode_verif=etat.methode_verif,
            template_path=etat.template_path,
            texte_ocr=etat.texte_ocr,
            threshold=etat.threshold
        )

    def sauvegarder(self, etat: EtatSchema, output_dir: Path) -> Path:
        """Sauvegarde le code généré dans un fichier"""
        code = self.generer(etat)
        filename = f"etat_{etat.nom}.py"
        filepath = output_dir / filename
        filepath.write_text(code, encoding="utf-8")
        return filepath
```

### 4.4 Template Jinja2 (etat.py.j2)

```jinja2
"""
État généré automatiquement par le Générateur de Classes.
Ne pas modifier manuellement - utilisez l'interface de génération.
"""
from core.etat import Etat


class {{ nom_classe }}(Etat):
    """État: {{ nom }}"""

    nom = "{{ nom }}"
    groupes = {{ groupes | tojson }}
    priorite = {{ priorite }}

    def verif(self, manoir) -> bool:
        """Vérifie si l'état est actif."""
{% if methode_verif == "image" %}
        return manoir.detect_image(
            "{{ template_path }}",
            threshold={{ threshold }}
        )
{% elif methode_verif == "texte" %}
        return manoir.detect_text("{{ texte_ocr }}")
{% elif methode_verif == "combinaison" %}
        image_ok = manoir.detect_image(
            "{{ template_path }}",
            threshold={{ threshold }}
        )
        texte_ok = manoir.detect_text("{{ texte_ocr }}")
        return image_ok and texte_ok
{% endif %}
```

---

## 5. Frontend

### 5.1 Structure des Fichiers

```
static/
├── css/
│   ├── main.css                # Styles principaux
│   ├── blockly-theme.css       # Thème Blockly personnalisé
│   └── components/
│       ├── image-editor.css    # Éditeur d'image
│       ├── form-elements.css   # Éléments de formulaire
│       └── preview.css         # Prévisualisation code
│
├── js/
│   ├── app.js                  # Point d'entrée application
│   ├── api.js                  # Client API REST
│   ├── state.js                # Gestion état application
│   │
│   ├── views/
│   │   ├── etat-view.js        # Vue création état
│   │   ├── chemin-view.js      # Vue création chemin
│   │   ├── action-view.js      # Vue création action
│   │   └── action-longue-view.js
│   │
│   ├── components/
│   │   ├── image-editor.js     # Éditeur/sélecteur de région
│   │   ├── code-preview.js     # Prévisualisation code
│   │   ├── tooltip.js          # Bulles d'aide
│   │   └── notification.js     # Notifications
│   │
│   └── blockly/
│       ├── blocks/             # Définitions blocs personnalisés
│       │   ├── action-blocks.js
│       │   ├── control-blocks.js
│       │   └── condition-blocks.js
│       ├── generators/         # Générateurs de code
│       │   └── python.js
│       └── toolbox.js          # Configuration toolbox
│
└── templates/
    ├── index.html              # Page principale
    ├── partials/
    │   ├── header.html
    │   ├── sidebar.html
    │   └── footer.html
    └── views/
        ├── etat.html
        ├── chemin.html
        ├── action.html
        └── action-longue.html
```

### 5.2 Composant Éditeur d'Image (image-editor.js)

```javascript
/**
 * Éditeur d'image pour la sélection de régions
 */
class ImageEditor {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            minWidth: 10,
            minHeight: 10,
            showGrid: false,
            ...options
        };

        this.canvas = null;
        this.ctx = null;
        this.image = null;
        this.selection = null;
        this.isDragging = false;

        this.init();
    }

    init() {
        this.canvas = document.createElement('canvas');
        this.ctx = this.canvas.getContext('2d');
        this.container.appendChild(this.canvas);

        this.setupEventListeners();
    }

    /**
     * Charge une image dans l'éditeur
     * @param {string} src - URL ou chemin de l'image
     */
    async loadImage(src) {
        return new Promise((resolve, reject) => {
            this.image = new Image();
            this.image.onload = () => {
                this.canvas.width = this.image.width;
                this.canvas.height = this.image.height;
                this.render();
                resolve();
            };
            this.image.onerror = reject;
            this.image.src = src;
        });
    }

    /**
     * Définit la sélection courante
     * @param {Object} region - {x, y, width, height}
     */
    setSelection(region) {
        this.selection = { ...region };
        this.render();
    }

    /**
     * Récupère la région sélectionnée
     * @returns {Object|null} - {x, y, width, height}
     */
    getSelection() {
        return this.selection ? { ...this.selection } : null;
    }

    /**
     * Affiche les suggestions de l'IA
     * @param {Array} suggestions - Liste des régions suggérées
     */
    showSuggestions(suggestions) {
        this.suggestions = suggestions;
        this.render();
    }

    render() {
        if (!this.image) return;

        // Dessiner l'image
        this.ctx.drawImage(this.image, 0, 0);

        // Dessiner les suggestions IA (en bleu semi-transparent)
        if (this.suggestions) {
            this.ctx.strokeStyle = 'rgba(0, 100, 255, 0.7)';
            this.ctx.lineWidth = 2;
            this.ctx.setLineDash([5, 5]);

            this.suggestions.forEach((s, i) => {
                this.ctx.strokeRect(s.x, s.y, s.width, s.height);
            });

            this.ctx.setLineDash([]);
        }

        // Dessiner la sélection courante (en vert)
        if (this.selection) {
            this.ctx.strokeStyle = '#00ff00';
            this.ctx.lineWidth = 2;
            this.ctx.strokeRect(
                this.selection.x,
                this.selection.y,
                this.selection.width,
                this.selection.height
            );

            // Poignées de redimensionnement
            this.drawHandles();
        }
    }

    setupEventListeners() {
        this.canvas.addEventListener('mousedown', this.onMouseDown.bind(this));
        this.canvas.addEventListener('mousemove', this.onMouseMove.bind(this));
        this.canvas.addEventListener('mouseup', this.onMouseUp.bind(this));
    }

    // ... autres méthodes d'interaction
}
```

### 5.3 Configuration Blockly (toolbox.js)

```javascript
/**
 * Configuration de la toolbox Blockly pour ActionLongue
 */
const toolboxConfig = {
    kind: 'categoryToolbox',
    contents: [
        {
            kind: 'category',
            name: 'Actions',
            colour: '#5b80a5',
            contents: [
                {
                    kind: 'block',
                    type: 'action_bouton'
                },
                {
                    kind: 'block',
                    type: 'action_attendre'
                },
                {
                    kind: 'block',
                    type: 'action_texte'
                }
            ]
        },
        {
            kind: 'category',
            name: 'Contrôle',
            colour: '#5ba55b',
            contents: [
                {
                    kind: 'block',
                    type: 'controls_if'
                },
                {
                    kind: 'block',
                    type: 'controls_repeat_ext'
                },
                {
                    kind: 'block',
                    type: 'controls_whileUntil'
                }
            ]
        },
        {
            kind: 'category',
            name: 'Conditions',
            colour: '#a55b80',
            contents: [
                {
                    kind: 'block',
                    type: 'condition_image_presente'
                },
                {
                    kind: 'block',
                    type: 'condition_texte_present'
                },
                {
                    kind: 'block',
                    type: 'condition_etat_actif'
                }
            ]
        },
        {
            kind: 'category',
            name: 'Erreurs',
            colour: '#a55b5b',
            contents: [
                {
                    kind: 'block',
                    type: 'gestion_erreur'
                },
                {
                    kind: 'block',
                    type: 'verifier_popup'
                }
            ]
        }
    ]
};

// Définition des blocs personnalisés
Blockly.Blocks['action_bouton'] = {
    init: function() {
        this.appendDummyInput()
            .appendField('Cliquer sur')
            .appendField(new Blockly.FieldTextInput('bouton.png'), 'TEMPLATE');
        this.appendDummyInput()
            .appendField('décalage X')
            .appendField(new Blockly.FieldNumber(0), 'OFFSET_X')
            .appendField('Y')
            .appendField(new Blockly.FieldNumber(0), 'OFFSET_Y');
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(230);
        this.setTooltip('Clique sur un élément identifié par une image template');
    }
};

Blockly.Blocks['condition_image_presente'] = {
    init: function() {
        this.appendDummyInput()
            .appendField('image présente')
            .appendField(new Blockly.FieldTextInput('image.png'), 'TEMPLATE');
        this.setOutput(true, 'Boolean');
        this.setColour(210);
        this.setTooltip('Vérifie si une image est présente à l\'écran');
    }
};
```

---

## 6. Service de Détection de Duplicatas

### 6.1 Algorithme

```python
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional

class DuplicateService:
    """Service de détection de templates similaires"""

    def __init__(self, templates_dir: Path, threshold: float = 0.90):
        self.templates_dir = templates_dir
        self.threshold = threshold
        self.hash_cache = {}

    def compute_hash(self, image_path: Path) -> str:
        """
        Calcule un hash perceptuel de l'image.
        Utilise dHash pour la robustesse aux petites variations.
        """
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)

        # Redimensionner à 9x8 pour calculer 64 bits de différence
        resized = cv2.resize(img, (9, 8), interpolation=cv2.INTER_AREA)

        # Calculer les différences horizontales
        diff = resized[:, 1:] > resized[:, :-1]

        # Convertir en hash hexadécimal
        return ''.join(['1' if b else '0' for b in diff.flatten()])

    def hamming_distance(self, hash1: str, hash2: str) -> int:
        """Calcule la distance de Hamming entre deux hashes"""
        return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))

    def find_similar(
        self,
        image_path: Path
    ) -> List[Tuple[Path, float]]:
        """
        Trouve les templates similaires à l'image donnée.

        Args:
            image_path: Chemin de l'image à comparer

        Returns:
            Liste de tuples (chemin_template, score_similarité)
        """
        new_hash = self.compute_hash(image_path)
        similar = []

        for template_path in self.templates_dir.rglob("*.png"):
            if template_path not in self.hash_cache:
                self.hash_cache[template_path] = self.compute_hash(template_path)

            existing_hash = self.hash_cache[template_path]
            distance = self.hamming_distance(new_hash, existing_hash)

            # Normaliser: 64 bits max de différence
            similarity = 1 - (distance / 64)

            if similarity >= self.threshold:
                similar.append((template_path, similarity))

        # Trier par similarité décroissante
        similar.sort(key=lambda x: x[1], reverse=True)
        return similar

    def template_match_similarity(
        self,
        image1: Path,
        image2: Path
    ) -> float:
        """
        Compare deux images avec template matching OpenCV.
        Plus précis mais plus lent.
        """
        img1 = cv2.imread(str(image1), cv2.IMREAD_GRAYSCALE)
        img2 = cv2.imread(str(image2), cv2.IMREAD_GRAYSCALE)

        # Redimensionner si nécessaire
        if img1.shape != img2.shape:
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

        result = cv2.matchTemplate(img1, img2, cv2.TM_CCOEFF_NORMED)
        return float(result[0][0])
```

---

## 7. Gestion des Erreurs

### 7.1 Codes d'Erreur API

| Code | Nom | Description |
|------|-----|-------------|
| `ERR_001` | `INVALID_IMAGE` | Image invalide ou corrompue |
| `ERR_002` | `REGION_OUT_OF_BOUNDS` | Région hors limites de l'image |
| `ERR_003` | `DUPLICATE_NAME` | Nom déjà utilisé |
| `ERR_004` | `STATE_NOT_FOUND` | État référencé introuvable |
| `ERR_005` | `TEMPLATE_DUPLICATE` | Template similaire existant |
| `ERR_006` | `CLAUDE_API_ERROR` | Erreur API Claude |
| `ERR_007` | `GENERATION_FAILED` | Échec de génération de code |
| `ERR_008` | `SESSION_EXPIRED` | Session de travail expirée |

### 7.2 Format de Réponse d'Erreur

```json
{
  "success": false,
  "error": {
    "code": "ERR_005",
    "message": "Un template similaire existe déjà",
    "details": {
      "existing_template": "genere/templates/menu/bouton_jouer.png",
      "similarity": 0.95
    },
    "suggestions": [
      "Utilisez le template existant",
      "Modifiez votre sélection pour la rendre plus distinctive",
      "Forcez la création si vous êtes sûr"
    ]
  }
}
```

---

## 8. Configuration

### 8.1 Fichier de Configuration (config.toml)

```toml
[server]
host = "127.0.0.1"
port = 8000
debug = false
reload = true

[paths]
upload_dir = "uploads"
generated_dir = "genere"
templates_dir = "genere/templates"
sessions_dir = "sessions"

[claude]
model = "claude-3-opus-20240229"
max_tokens = 2048
timeout = 30

[detection]
default_threshold = 0.8
min_threshold = 0.5
max_threshold = 1.0
duplicate_threshold = 0.90

[ocr]
lang = "fra"
psm = 3

[defaults]
popup_priority = 80
normal_priority = 0
default_delay_after = 0.1

[blockly]
theme = "dark"
grid_spacing = 20
zoom_controls = true
```

### 8.2 Variables d'Environnement

```bash
# .env
CLAUDE_API_KEY=sk-ant-...
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./generateur.db
LOG_LEVEL=INFO
```

---

## 9. Tests

### 9.1 Structure des Tests

```
tests/
├── __init__.py
├── conftest.py                  # Fixtures pytest
│
├── unit/
│   ├── test_etat_generator.py
│   ├── test_chemin_generator.py
│   ├── test_action_generator.py
│   ├── test_duplicate_service.py
│   └── test_blockly_parser.py
│
├── integration/
│   ├── test_api_etats.py
│   ├── test_api_chemins.py
│   ├── test_api_actions.py
│   └── test_claude_service.py
│
└── e2e/
    ├── test_workflow_etat.py
    ├── test_workflow_chemin.py
    └── test_workflow_action_longue.py
```

### 9.2 Exemple de Test Unitaire

```python
import pytest
from pathlib import Path
from generateur.generators.etat_generator import EtatGenerator
from generateur.models.schemas import EtatSchema, MethodeVerification

class TestEtatGenerator:
    @pytest.fixture
    def generator(self, tmp_path):
        templates_dir = Path(__file__).parent.parent / "generators" / "templates"
        return EtatGenerator(templates_dir)

    @pytest.fixture
    def etat_simple(self):
        return EtatSchema(
            nom="test_ville",
            nom_classe="EtatTestVille",
            groupes=["test"],
            priorite=0,
            methode_verif=MethodeVerification.IMAGE,
            template_path="templates/test/ville.png",
            threshold=0.85,
            image_source="/tmp/source.png"
        )

    def test_generer_etat_image(self, generator, etat_simple):
        code = generator.generer(etat_simple)

        assert "class EtatTestVille(Etat):" in code
        assert 'nom = "test_ville"' in code
        assert 'groupes = ["test"]' in code
        assert "detect_image" in code
        assert "threshold=0.85" in code

    def test_generer_etat_texte(self, generator, etat_simple):
        etat_simple.methode_verif = MethodeVerification.TEXTE
        etat_simple.texte_ocr = "Menu Principal"

        code = generator.generer(etat_simple)

        assert "detect_text" in code
        assert "Menu Principal" in code
```

---

## 10. Déploiement

### 10.1 Prérequis Système

- Python 3.11+
- Tesseract OCR installé
- 4 Go RAM minimum
- Connexion internet (pour API Claude)

### 10.2 Installation

```bash
# Cloner le projet
git clone <repository>
cd generateur

# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate   # Windows

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec votre clé API Claude

# Lancer le serveur
uvicorn generateur.main:app --reload
```

### 10.3 Requirements

```
# requirements.txt
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
pydantic>=2.0.0
python-multipart>=0.0.6
jinja2>=3.1.0
anthropic>=0.18.0
opencv-python>=4.8.0
pillow>=10.0.0
pytesseract>=0.3.10
aiosqlite>=0.19.0
python-dotenv>=1.0.0
tomli>=2.0.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
httpx>=0.24.0
```

---

## 11. Sécurité

### 11.1 Considérations

- **Validation des entrées**: Tous les chemins de fichiers sont validés pour éviter les path traversal
- **Limite de taille**: Upload d'images limité à 10 Mo
- **Rate limiting**: API Claude limitée à 10 requêtes/minute
- **Sanitization**: Noms de fichiers générés sont sanitizés
- **CORS**: Configuré pour localhost uniquement en développement

### 11.2 Validation des Chemins

```python
from pathlib import Path
import re

def validate_filename(name: str) -> bool:
    """Valide un nom de fichier"""
    pattern = r'^[a-z][a-z0-9_]{0,49}$'
    return bool(re.match(pattern, name))

def safe_path(base_dir: Path, user_input: str) -> Path:
    """Construit un chemin sécurisé"""
    base = base_dir.resolve()
    target = (base / user_input).resolve()

    if not target.is_relative_to(base):
        raise ValueError("Path traversal détecté")

    return target
```

---

*Document généré le 27/12/2025*
*Version 1.0*
