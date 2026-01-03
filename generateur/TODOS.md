# TODOS - Générateur de Classes

## Phase 1 - MVP (Minimum Viable Product) ✅

### Backend
- [x] Structure du projet FastAPI
- [x] Configuration et variables d'environnement
- [x] Schémas Pydantic (EtatCreate, CheminCreate, ActionReference)
- [x] Service de gestion des images (upload, crop, hash)
- [x] Service de gestion des états
- [x] Service de gestion des chemins
- [x] Service Claude (intégration API)
- [x] Générateur de code états (Jinja2)
- [x] Générateur de code chemins (Jinja2)
- [x] Routes API REST (états, chemins, images, IA)

### Frontend
- [x] Interface d'accueil
- [x] Page création d'état
- [x] Page création de chemin
- [x] Éditeur d'image avec sélection de région
- [x] Prévisualisation du code généré
- [x] Système de tags pour les groupes
- [x] Client API JavaScript

### Documentation
- [x] CLAUDE.md

---

## Phase 2 - Fonctionnalités Avancées ✅

### ActionLongue avec Blockly ✅
- [x] Intégrer la bibliothèque Blockly
- [x] Créer les blocs personnalisés :
  - [x] Bloc ActionBouton
  - [x] Bloc ActionAttendre
  - [x] Bloc ActionTexte
  - [x] Bloc ActionClicPosition
- [x] Créer les blocs de contrôle :
  - [x] Bloc Si / Si-Sinon
  - [x] Bloc Répéter (for)
  - [x] Bloc Tant que (while)
  - [x] Bloc Pour chaque (foreach)
- [x] Créer les blocs de conditions :
  - [x] image_presente / image_absente
  - [x] texte_present / texte_absent
  - [x] variable_egale / superieure / inferieure
  - [x] Combinateurs : et, ou, non
- [x] Générateur Blockly → Python
- [x] Service ActionLongue (création, validation)
- [x] Interface web pour ActionLongue
- [x] Sauvegarde/chargement du workspace Blockly

### Gestion des erreurs ✅
- [x] Charger la liste des erreurs existantes (liste_erreurs.py)
- [x] Interface de sélection des erreurs pour les actions
- [x] Création de nouvelles erreurs depuis l'interface
- [x] Suggestion d'erreurs par l'IA selon le contexte
- [x] Paramètres erreurs_verif_apres / erreurs_si_echec
- [x] Option retry_si_erreur_non_identifiee

### Améliorations UX ✅
- [x] Historique undo/redo (intégré à Blockly)
- [x] Drag & drop pour réordonner les actions (chemins)
- [x] Duplication d'actions
- [x] Raccourcis clavier
- [x] Mode sombre (thème par défaut)

---

## Phase 3 - Import et Synchronisation (En cours)

### Import des éléments existants
- [x] Parser les fichiers Python existants :
  - [x] Extraire les classes Etat
  - [x] Extraire les classes Chemin
  - [x] Extraire les classes Action
- [x] Afficher les éléments importés dans l'interface
- [x] Permettre la modification des éléments importés
- [x] Détecter les templates associés
- [x] API routes pour l'import (/api/import/*)
- [x] Détection des templates orphelins et manquants

### Synchronisation bidirectionnelle
- [ ] Détecter les modifications manuelles du code
- [ ] Mettre à jour l'interface si le code a changé
- [ ] Mettre à jour le code si l'interface a changé
- [ ] Gestion des conflits
- [ ] Versioning des fichiers générés

### Détection de duplicatas ✅
- [x] Hash perceptuel des images (dHash)
- [x] Comparaison avec templates existants
- [x] Avertissement si template similaire
- [x] Proposition d'utiliser l'existant
- [x] Forcer la création si nécessaire

### Base de données ✅
- [x] SQLite pour stocker les métadonnées
- [x] Table des sessions (brouillons)
- [x] Table des templates avec hash
- [x] Table des groupes
- [x] Table des erreurs connues
- [x] Recherche et filtrage

---

## Phase 4 - Améliorations et Optimisations

### Modèle local (optionnel)
- [ ] Intégration d'un modèle léger (ex: llama.cpp)
- [ ] Détection d'éléments sans connexion internet
- [ ] Fallback automatique si API indisponible

### Optimisations
- [ ] Cache des analyses IA
- [ ] Compression des images uploadées
- [ ] Lazy loading des templates
- [ ] Pagination des listes
- [ ] Optimisation du rendu canvas

### Tests
- [ ] Tests unitaires services
- [ ] Tests unitaires générateurs
- [ ] Tests d'intégration API
- [ ] Tests end-to-end (Playwright/Selenium)
- [ ] Couverture de code > 80%

### Nouveaux types d'actions
- [ ] ActionGlisser (drag & drop)
- [ ] ActionZoom (pinch)
- [ ] ActionSwipe
- [ ] ActionMultiClic
- [ ] ActionConditionMultiple

### Fonctionnalités supplémentaires
- [ ] Export/import de configuration (JSON)
- [ ] Templates prédéfinis (popup, menu, etc.)
- [ ] Mode batch (création multiple)
- [ ] Statistiques d'utilisation
- [ ] Logs des générations

---

## Bugs connus à corriger

- [ ] (Aucun pour l'instant)

---

## Notes techniques

### Dépendances à ajouter pour Phase 2
```
# Blockly (CDN ou npm)
# Pas de package Python, intégration frontend uniquement
```

### Dépendances à ajouter pour Phase 3
```
# Parser Python
ast (stdlib)
# ou lib externe pour parsing avancé
```

### Dépendances à ajouter pour Phase 4
```
# Modèle local
llama-cpp-python
# ou
transformers + torch
```

---

## Priorités suggérées

1. **Haute** : Phase 2 - Blockly et ActionLongue (valeur ajoutée majeure)
2. **Moyenne** : Phase 3 - Import existants (facilite l'adoption)
3. **Basse** : Phase 4 - Optimisations (amélioration continue)

---

*Dernière mise à jour : 03/01/2026*
