# Cahier des Charges - Générateur de Classes (État, Chemin, Action)

## 1. Présentation du Projet

### 1.1 Objectif
Créer un programme permettant de générer automatiquement les classes `Etat`, `Chemin`, `Action` et `ActionLongue` à partir d'images, avec une interface utilisateur intuitive et une assistance IA.

### 1.2 Contexte
Ce programme s'intègre au framework d'automatisation Mafia City existant. Il facilite la création des éléments nécessaires à l'automatisation sans avoir à écrire le code manuellement.

---

## 2. Spécifications Fonctionnelles

### 2.1 Source des Images

| Spécification | Valeur |
|---------------|--------|
| Source | Captures d'écran manuelles déposées dans un dossier |
| Format | PNG (format capture Windows standard) |
| Organisation | Workflow interactif (le programme demande pour chaque image) |

### 2.2 Interface Utilisateur

| Spécification | Valeur |
|---------------|--------|
| Type | Interface web (Flask/FastAPI + navigateur) |
| Langue | Français uniquement |
| Aide | Bulles d'aide au survol des éléments |
| Blocs visuels | Bibliothèque Blockly pour les structures de contrôle |

### 2.3 Génération des États (Etat)

#### Workflow de création
1. L'utilisateur charge une image
2. Le programme demande le nom de l'état
3. L'IA (Claude) suggère :
   - Une zone d'image caractéristique (template) pour la détection
   - Un texte caractéristique (OCR) pour la détection
4. L'utilisateur valide ou ajuste la suggestion

#### Méthodes de vérification (`verif()`)
- **Image seule** : détection de template
- **Texte seul** : détection OCR
- **Combinaison** : image ET texte (les deux doivent être présents)
- Choix flexible selon l'état

#### Groupes d'états
- L'IA suggère un groupe basé sur l'image
- Liste des groupes existants proposée
- Possibilité de créer de nouveaux groupes

#### Priorités
- L'IA suggère une priorité (popups en haute priorité)
- L'utilisateur peut modifier la suggestion

### 2.4 Génération des Chemins (Chemin)

#### Workflow de création
1. L'utilisateur indique l'état de départ (nom)
2. L'utilisateur indique l'état d'arrivée (nom)
3. L'utilisateur montre sur l'image l'élément à cliquer
4. Ajout séquentiel des actions ("Ajouter une autre action?")

#### États de sortie incertains
- Le programme demande : "Y a-t-il plusieurs états de sortie possibles?"
- Suggestion automatique des états d'erreur/popup connus
- L'utilisateur peut lister les états de sortie possibles

### 2.5 Génération des Actions

#### Types d'actions supportés
| Type | Description |
|------|-------------|
| `ActionBouton` | Clic sur une image/template |
| `ActionAttendre` | Délai/pause |
| `ActionTexte` | Clic sur un texte détecté par OCR |
| `ActionLongue` | Action interruptible de longue durée |

**Architecture extensible** pour ajouter facilement d'autres types d'actions.

#### Définition des zones cliquables
1. L'utilisateur clique sur le centre du bouton
2. Le programme découpe automatiquement autour
3. L'IA peut suggérer des zones cliquables
4. L'utilisateur peut ajuster manuellement le découpage

#### Taille des templates
- Découpage intelligent par l'IA (basé sur l'élément détecté)
- Ajustable manuellement avec un rectangle

#### Offset et précision
- Clic au centre par défaut
- Possibilité de définir un décalage X/Y si besoin

#### Seuil de confiance (threshold)
- Valeur par défaut : 0.8
- Ajustable par template si nécessaire
- Le programme peut tester et suggérer un seuil optimal

#### Conditions d'exécution
- Système similaire à `verif()` des états (image/texte)
- Interface avec blocs visuels
- L'IA propose des conditions basées sur le contexte

#### Délais et timings
- Valeurs par défaut ajustables

### 2.6 Génération des ActionLongue

#### Structure
| Élément | Description |
|---------|-------------|
| État d'entrée | État requis pour exécuter l'action |
| Séquence d'actions | Liste d'actions à exécuter une par une |
| Structures de contrôle | if, loop, switch... (blocs visuels Blockly) |
| État de sortie | Même que l'entrée (sauf popup/erreur) |

#### Interface
- Éditeur de blocs visuels type Scratch (Blockly)
- Glisser-déposer des actions et structures de contrôle

### 2.7 Gestion des Erreurs

- Proposition des erreurs connues (depuis `liste_erreurs.py`)
- Création de nouvelles erreurs avec images/textes
- L'IA suggère des erreurs potentielles basées sur le contexte

---

## 3. Spécifications Techniques

### 3.1 Fichiers Générés

| Type | Emplacement |
|------|-------------|
| Code Python | Dossier séparé "généré" |
| Configuration | Dossier séparé "généré" |
| Templates images | Dossier séparé "généré" |

L'utilisateur déplace manuellement les fichiers vers les emplacements définitifs.

### 3.2 Nommage

- Automatique basé sur le nom donné
- Exemple : état "Ville" → `etat_ville.py`, `class EtatVille`
- Personnalisation possible

### 3.3 Manoirs

- Création d'éléments génériques
- L'association aux manoirs se fait ailleurs (dans le code existant)

### 3.4 Détection de Duplicatas

- Avertissement si un template ressemble à un existant
- Proposition d'utiliser l'existant
- Création forcée possible si nécessaire

---

## 4. Intégration IA (Claude)

### 4.1 Fonctionnalités IA

| Fonctionnalité | Description |
|----------------|-------------|
| Découpage d'images | Suggérer la zone caractéristique d'un état |
| Détection de texte | Identifier le texte caractéristique |
| Groupes | Suggérer le groupe approprié |
| Priorités | Suggérer la priorité de l'état |
| Erreurs | Suggérer les erreurs potentielles |
| Conditions | Proposer des conditions basées sur le contexte |
| Zones cliquables | Détecter les boutons/éléments interactifs |
| Seuil optimal | Suggérer le threshold de détection |

### 4.2 Architecture

- **Phase 1** : API Claude (connexion internet + clé API requises)
- **Phase 2** (ultérieure) : Possibilité d'ajouter un modèle local léger

---

## 5. Prévisualisation et Validation

### 5.1 Avant génération
- Aperçu du code Python qui sera généré
- Simulation du chemin/action sans exécution réelle

### 5.2 Sauvegarde
- Demande de confirmation pour sauvegarder les brouillons
- Possibilité de reprendre un travail non terminé

---

## 6. Édition et Import

### 6.1 Modification des éléments créés
- Édition via l'interface (rouvrir et modifier)
- Édition directe du code Python généré
- Les deux méthodes disponibles

### 6.2 Import des éléments existants
- Import et affichage des états/chemins/actions existants
- Modification possible depuis l'interface
- Synchronisation si le code est modifié manuellement

---

## 7. Résumé des Choix Techniques

| Composant | Technologie |
|-----------|-------------|
| Backend | Python (Flask ou FastAPI) |
| Frontend | HTML/CSS/JavaScript |
| Blocs visuels | Google Blockly |
| IA | API Claude (Anthropic) |
| Format images | PNG |
| Configuration | JSON/TOML |

---

## 8. Priorités de Développement

### Phase 1 - MVP (Minimum Viable Product)
1. Interface web basique
2. Création d'états simples (image OU texte)
3. Création de chemins simples (une action)
4. Génération du code Python
5. Intégration API Claude basique

### Phase 2 - Fonctionnalités Avancées
1. ActionLongue avec blocs visuels (Blockly)
2. Structures de contrôle (if, loop)
3. Conditions d'exécution avancées
4. Gestion des erreurs complète

### Phase 3 - Import et Synchronisation
1. Import des éléments existants
2. Synchronisation bidirectionnelle code/interface
3. Détection de duplicatas

### Phase 4 - Améliorations
1. Modèle local optionnel
2. Optimisations de performance
3. Nouveaux types d'actions

---

## 9. Annexes

### 9.1 Classes Existantes à Générer

```python
# Etat (exemple)
class EtatVille(Etat):
    nom = "ville"
    groupes = ["ecran_principal"]

    def verif(self, manoir) -> bool:
        return manoir.detect_image("ville/icone.png")

# Chemin (exemple)
class CheminLancerJeu(Chemin):
    etat_initial = "non_lance"
    etat_sortie = "chargement"

    def fonction_actions(self, manoir) -> List[Any]:
        return [
            ActionBouton(manoir, "bouton_lancer.png"),
            ActionAttendre(manoir, 5),
        ]

# Action (exemple)
class ActionBouton(Action):
    def __init__(self, fenetre, template_path, offset=(0, 0)):
        super().__init__(fenetre)
        self.template_path = template_path
        self.offset = offset
```

### 9.2 Structure du Dossier Généré

```
genere/
├── etats/
│   ├── etat_xxx.py
│   └── ...
├── chemins/
│   ├── chemin_xxx.py
│   └── ...
├── actions/
│   ├── action_xxx.py
│   └── ...
├── templates/
│   ├── xxx/
│   │   ├── element.png
│   │   └── ...
│   └── ...
└── config/
    └── generated_config.toml
```

---

*Document généré le 27/12/2025*
*Version 1.0*
