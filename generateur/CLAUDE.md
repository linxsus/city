# CLAUDE.md - Générateur de Classes

## Aperçu

Application web pour générer automatiquement les classes **Etat**, **Chemin** et **Action** du framework d'automatisation Mafia City.

## Lancement

```bash
# Installer les dépendances
pip install -r requirements.txt

# Lancer le serveur
python -m generateur.main

# Interface web
http://127.0.0.1:8000

# Documentation API
http://127.0.0.1:8000/docs
```

## Structure du projet

```
generateur/
├── main.py                 # Point d'entrée FastAPI
├── config.py               # Configuration (lit .env)
├── requirements.txt        # Dépendances Python
│
├── api/routes/             # Endpoints REST
│   ├── etats.py            # /api/etats/*
│   ├── chemins.py          # /api/chemins/*
│   ├── images.py           # /api/images/*
│   └── ia.py               # /api/ia/*
│
├── services/               # Logique métier
│   ├── etat_service.py     # Création/validation états
│   ├── chemin_service.py   # Création/validation chemins
│   ├── image_service.py    # Upload, crop, hash images
│   └── claude_service.py   # Intégration API Claude
│
├── generators/             # Génération de code Python
│   ├── etat_generator.py
│   ├── chemin_generator.py
│   └── templates/          # Templates Jinja2
│       ├── etat.py.j2
│       └── chemin.py.j2
│
├── models/
│   └── schemas.py          # Schémas Pydantic
│
├── static/                 # Assets frontend
│   ├── css/main.css
│   └── js/
│       ├── api.js          # Client API
│       ├── app.js          # Utils globaux
│       ├── components/
│       │   └── image-editor.js  # Éditeur de sélection
│       └── views/
│           ├── etat-view.js
│           └── chemin-view.js
│
├── templates/              # Templates HTML (Jinja2)
│   ├── index.html
│   ├── partials/
│   └── views/
│
├── uploads/                # Images uploadées (temp)
├── genere/                 # Fichiers générés
│   ├── etats/              # Code Python des états
│   ├── chemins/            # Code Python des chemins
│   └── templates/          # Images templates découpées
│
└── sessions/               # Brouillons sauvegardés
```

## Configuration

### Variables d'environnement (.env)

```bash
# Copier le template
cp .env.example .env
```

| Variable | Description | Requis |
|----------|-------------|--------|
| `ANTHROPIC_API_KEY` | Clé API Claude (sk-ant-...) | Non* |
| `SECRET_KEY` | Clé secrète sessions | Non |
| `DEBUG` | Mode debug (true/false) | Non |
| `HOST` | Adresse serveur | Non |
| `PORT` | Port serveur | Non |

*Sans clé API, les suggestions IA sont désactivées mais l'app fonctionne en mode manuel.

## API REST

### États

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/etats/groups` | Liste des groupes existants |
| GET | `/api/etats/existing` | Liste des états existants |
| POST | `/api/etats/validate` | Valide les données |
| POST | `/api/etats/preview` | Prévisualise le code |
| POST | `/api/etats/create` | Crée l'état et génère le code |

### Chemins

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/chemins/states` | États disponibles |
| POST | `/api/chemins/suggest-exits` | Suggère états de sortie |
| POST | `/api/chemins/validate` | Valide les données |
| POST | `/api/chemins/preview` | Prévisualise le code |
| POST | `/api/chemins/create` | Crée le chemin |

### Images

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/images/upload` | Upload une image |
| GET | `/api/images/serve?path=` | Sert une image |
| POST | `/api/images/crop` | Découpe une région |
| GET | `/api/images/info?path=` | Info sur une image |

### IA (Claude)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/ia/status` | Vérifie si Claude est disponible |
| POST | `/api/ia/analyze` | Analyse une image |
| POST | `/api/ia/detect-buttons` | Détecte les zones cliquables |

## Schémas de données

### EtatCreate

```python
{
    "nom": "ville_principale",      # snake_case, unique
    "groupes": ["ecran_principal"],
    "priorite": 0,                  # 0=normal, 80-100=popup
    "methode_verif": "image",       # image | texte | combinaison
    "template_region": {            # Si méthode image/combinaison
        "x": 100, "y": 50,
        "width": 200, "height": 100
    },
    "texte_ocr": "Menu",            # Si méthode texte/combinaison
    "threshold": 0.8,               # 0.5 - 1.0
    "image_source": "/path/to/image.png",
    "description": "Description optionnelle"
}
```

### CheminCreate

```python
{
    "nom": "ville_vers_carte",
    "etat_initial": "ville",
    "etat_sortie": "carte",
    "etats_sortie_possibles": ["popup_erreur"],
    "actions": [
        {
            "type": "ActionBouton",
            "parametres": {
                "template_path": "boutons/carte.png",
                "threshold": 0.8
            },
            "ordre": 0
        },
        {
            "type": "ActionAttendre",
            "parametres": {"duree": 2},
            "ordre": 1
        }
    ]
}
```

## Code généré

### Exemple d'état généré

```python
# genere/etats/etat_ville_principale.py
from core.etat import Etat

class EtatVillePrincipale(Etat):
    nom = "ville_principale"
    groupes = ["ecran_principal"]
    priorite = 0

    def verif(self, manoir) -> bool:
        return manoir.detect_image(
            "ville_principale/template.png",
            threshold=0.8
        )
```

### Exemple de chemin généré

```python
# genere/chemins/chemin_ville_vers_carte.py
from core.chemin import Chemin
from actions.simple.action_bouton import ActionBouton
from actions.simple.action_attendre import ActionAttendre

class CheminVilleVersCarte(Chemin):
    etat_initial = "ville"
    etat_sortie = "carte"

    def fonction_actions(self, manoir) -> list:
        return [
            ActionBouton(manoir, "boutons/carte.png", threshold=0.8),
            ActionAttendre(manoir, 2),
        ]
```

## Intégration Claude

Le service Claude analyse les images pour suggérer :

1. **Régions caractéristiques** - Zones uniques pour identifier l'écran
2. **Textes détectés** - Textes importants visibles
3. **Groupe suggéré** - Basé sur le type d'écran
4. **Priorité suggérée** - Haute pour les popups
5. **Zones cliquables** - Boutons et éléments interactifs

### Prompt d'analyse

L'IA reçoit l'image et retourne un JSON structuré avec ses suggestions. L'utilisateur peut accepter, modifier ou ignorer ces suggestions.

## Développement

### Ajouter un nouveau type d'action

1. Ajouter le schéma dans `models/schemas.py`
2. Ajouter la génération dans `generators/chemin_generator.py`
3. Ajouter le formulaire dans `static/js/views/chemin-view.js`

### Conventions

- **Backend** : Python 3.11+, FastAPI, Pydantic v2
- **Frontend** : Vanilla JS (pas de framework)
- **Nommage** : snake_case (Python), camelCase (JS)

## Phases de développement

- [x] **Phase 1 - MVP** : États simples, chemins simples, génération code
- [ ] **Phase 2** : ActionLongue avec Blockly, structures de contrôle
- [ ] **Phase 3** : Import/synchronisation avec code existant
- [ ] **Phase 4** : Modèle local optionnel, optimisations
