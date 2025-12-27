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

## Phase 2 - Fonctionnalités Avancées

### ActionLongue avec Blockly
- [ ] Intégrer la bibliothèque Blockly
- [ ] Créer les blocs personnalisés :
  - [ ] Bloc ActionBouton
  - [ ] Bloc ActionAttendre
  - [ ] Bloc ActionTexte
  - [ ] Bloc ActionSimple (lambda)
- [ ] Créer les blocs de contrôle :
  - [ ] Bloc If / If-Else
  - [ ] Bloc For (boucle comptée)
  - [ ] Bloc While (boucle conditionnelle)
  - [ ] Bloc Switch / Case
- [ ] Créer les blocs de conditions :
  - [ ] image_presente / image_absente
  - [ ] texte_present / texte_absent
  - [ ] variable_egale / superieure / inferieure
  - [ ] Combinateurs : et, ou, non
- [ ] Parser Blockly → Structure Python
- [ ] Générateur de code ActionLongue
- [ ] Template Jinja2 pour ActionLongue
- [ ] Interface web pour ActionLongue
- [ ] Sauvegarde/chargement du workspace Blockly

### Gestion des erreurs
- [ ] Charger la liste des erreurs existantes (liste_erreurs.py)
- [ ] Interface de sélection des erreurs pour les actions
- [ ] Création de nouvelles erreurs depuis l'interface
- [ ] Suggestion d'erreurs par l'IA selon le contexte
- [ ] Paramètres erreurs_verif_apres / erreurs_si_echec
- [ ] Option retry_si_erreur_non_identifiee

### Conditions d'exécution
- [ ] Interface visuelle pour les conditions (condition_func)
- [ ] Blocs Blockly pour les conditions
- [ ] Prévisualisation des conditions générées

### Améliorations UX
- [ ] Drag & drop pour réordonner les actions
- [ ] Duplication d'actions
- [ ] Historique undo/redo
- [ ] Raccourcis clavier
- [ ] Mode sombre / clair

---

## Phase 3 - Import et Synchronisation

### Import des éléments existants
- [ ] Parser les fichiers Python existants :
  - [ ] Extraire les classes Etat
  - [ ] Extraire les classes Chemin
  - [ ] Extraire les classes Action
- [ ] Afficher les éléments importés dans l'interface
- [ ] Permettre la modification des éléments importés
- [ ] Détecter les templates associés

### Synchronisation bidirectionnelle
- [ ] Détecter les modifications manuelles du code
- [ ] Mettre à jour l'interface si le code a changé
- [ ] Mettre à jour le code si l'interface a changé
- [ ] Gestion des conflits
- [ ] Versioning des fichiers générés

### Détection de duplicatas
- [ ] Hash perceptuel des images (dHash)
- [ ] Comparaison avec templates existants
- [ ] Avertissement si template similaire
- [ ] Proposition d'utiliser l'existant
- [ ] Forcer la création si nécessaire

### Base de données
- [ ] SQLite pour stocker les métadonnées
- [ ] Table des sessions (brouillons)
- [ ] Table des templates avec hash
- [ ] Table des groupes
- [ ] Table des erreurs connues
- [ ] Recherche et filtrage

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

*Dernière mise à jour : 27/12/2025*
