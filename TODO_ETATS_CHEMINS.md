# TODO - Système États/Chemins

## État actuel
Le système de base est implémenté. Il reste quelques tâches pour finaliser l'intégration.

---

## 1. Créer `ActionBouton` ✅

- [x] Créer `actions/simple/action_bouton.py`
  - Clic sur une image (template_path)
  - Hérite de Action
  - Paramètres : fenetre, template_path, offset=(0,0), threshold=None
  - `condition()` vérifie si l'image est visible et stocke la position
  - `_run()` clique sur la position stockée (1 seule détection)

- [x] Ajouter l'export dans `actions/liste_actions.py`

```python
# Exemple d'utilisation
ActionBouton(manoir, "boutons/bouton_gratuit.png")
```

---

## 2. Classe Popup unifiée ✅

Créer une classe `Popup` qui hérite de `Etat` et génère automatiquement son `Chemin` de fermeture.

- [x] Créer `core/popup.py` avec classes `Popup` et `CheminPopup`
  - `Popup` hérite de `Etat`
  - Attributs: `image_detection`, `image_fermeture`, `position_fermeture`, `position_relative`, `etats_possibles_apres`
  - Méthode `generer_chemin()` retourne un `CheminPopup`
  - `CheminPopup` génère automatiquement les actions (ActionBouton ou clic positionnel)

- [x] Modifier `GestionnaireEtats._scanner_etats()` pour auto-générer les chemins
  - Détecte les instances de `Popup`
  - Appelle `generer_chemin()` et ajoute le chemin à `_chemins`

- [x] Migrer les popups existants vers la nouvelle classe
  - `etat_popup_gratuit.py` → hérite de `Popup`
  - `etat_popup_connexion.py` → hérite de `Popup`
  - `etat_popup_rapport.py` → hérite de `Popup` (avec `position_fermeture`)

- [x] Supprimer les anciens fichiers chemins manuels
  - ✓ `chemin_fermer_popup_rapport.py` supprimé
  - ✓ `chemin_fermer_popup_connexion.py` supprimé
  - ✓ `chemin_fermer_popup_gratuit.py` supprimé

```python
# Exemple d'utilisation - définir un popup
class EtatPopupGratuit(Popup):
    nom = "popup_gratuit"
    image_detection = "boutons/bouton_gratuit.png"
    etats_possibles_apres = ["ville", "popup_rapport", "popup_connexion"]

# Le chemin est généré automatiquement par GestionnaireEtats
```

---

## 3. Actions legacy (optionnel)

Le dossier `actions/popups/` n'existe pas. Ces actions étaient référencées dans l'ancien code :

- [ ] `ActionFermerRapportDeveloppement`
- [ ] `ActionCollecterConnexionQuotidienne`
- [ ] `ActionClicBoutonGratuit`

**Note** : Probablement plus nécessaires si `ActionBouton` suffit pour les chemins.

---

## 4. Tests et validation

- [ ] Tester le flux complet : non_lance → ville
- [ ] Vérifier que les popups sont bien fermés
- [ ] Vérifier que le timeout fonctionne toujours
- [ ] Vérifier que `_etats_a_tester_apres_reprise` limite bien les états testés

---

## 5. ActionLongue avec `etat_requis` ✅

- [x] Ajouter paramètre `etat_requis` à `ActionLongue`
  - État dans lequel le manoir doit être pour exécuter l'action longue
  - Le manoir vérifie et navigue vers cet état avant d'ajouter l'action

```python
# Exemple d'utilisation
ActionLongue(manoir, [...], nom="tuer_mercenaire", etat_requis="ville")
```

---

## 6. Modifier ManoirBase pour gérer `etat_requis` ✅

- [x] Ajouter méthode `ajouter_action_longue(action_longue)` dans `ManoirBase`
  - Vérifie si `action_longue.etat_requis` est défini
  - Si oui, compare avec `self.etat_actuel`
  - Si différent, appelle `self.naviguer_vers(action_longue.etat_requis)`
  - Puis ajoute l'action à la séquence

```python
# Logique attendue dans ManoirBase
def ajouter_action_longue(self, action_longue):
    if action_longue.etat_requis:
        if self.etat_actuel != action_longue.etat_requis:
            self.naviguer_vers(action_longue.etat_requis)
    self.sequence.ajouter(action_longue)
```

---

## 7. Refactorer preparer_tour dans ManoirBase ✅

- [x] Restructurer `preparer_tour()` avec dispatch selon contexte
  - `_detecter_erreur()` → `_gerer_erreur()` (erreur détectée)
  - `_actif == False` → `_preparer_reprise_changement()` (changement de manoir)
  - `sequence.is_end()` → `_preparer_alimenter_sequence()` (séquence vide)
- [x] Ajouter `_actif = False` dans `__init__` et `reset()`
- [x] Adapter `ManoirBlueStacks` avec les nouvelles méthodes
- [x] Adapter `ManoirVirtuel` avec `_preparer_alimenter_sequence()`

```python
# Structure de preparer_tour
def preparer_tour(self):
    if self._detecter_erreur():
        return self._gerer_erreur()
    if not self._actif:
        self._actif = True
        return self._preparer_reprise_changement()
    if self.sequence.is_end():
        return self._preparer_alimenter_sequence()
    return True
```

---

## 8. Modifier Engine pour gérer _actif ✅

- [x] Quand Engine change de manoir actif :
  - `ancien_manoir._actif = False` dans `_changer_manoir()`
- [x] Vérifier que si séquence vide, Engine redemande `preparer_tour()`
  - ✓ `preparer_tour()` vérifie `sequence.is_end()` et appelle `_preparer_alimenter_sequence()`
- [x] Supprimer le passage de `raison` (plus nécessaire avec le flag `_actif`)
  - ✓ Non implémenté, donc rien à supprimer

---

## 9. Gestion des erreurs ✅

Implémenté dans ManoirBlueStacks :

- [x] État d'erreur : `EtatBlueStacks.BLOQUE`
- [x] `_detecter_erreur()` : retourne `True` si état == BLOQUE
- [x] `_gerer_erreur()` : appelle `_reboot_bluestacks()` et retourne `False`
- [x] `_reboot_bluestacks()` : ferme la fenêtre BlueStacks via WM_CLOSE, reset les flags

ManoirVirtuel n'a pas besoin de gestion d'erreur (toujours valide).

---

## 10. Appels activate() - Analyse ✅

Analyse des appels `activate()` maintenant que `_hook_reprise_changement()` l'appelle :

- [x] `manoir_bluestacks.py:317` - dans `_preparer_alimenter_sequence()` quand état = destination
  - ✓ **Partiellement redondant** : si on vient d'un changement de manoir, le hook l'a déjà appelé
  - ✓ **Nécessaire** : si le manoir continue sans changement, c'est le seul appel
  - ✓ **Conservé** : activate() est idempotent, double appel sans danger

- [x] `action_verifier_pret.py:61` - action legacy
  - ✓ **Non utilisée** : le nouveau système états/chemins remplace cette action
  - ✓ **Conservée** pour compatibilité

- [x] `action_verifier_pret_rapide.py:126` - action legacy
  - ✓ **Non utilisée** : le nouveau système états/chemins remplace cette action
  - ✓ **Conservée** pour compatibilité

---

## Référence - Fichiers clés

| Fichier | Rôle |
|---------|------|
| `core/etat.py` | Classe de base Etat avec verif(manoir) |
| `core/chemin.py` | Classe de base Chemin avec fonction_actions(manoir) |
| `core/popup.py` | Classe Popup (hérite Etat) + CheminPopup (auto-généré) |
| `core/etat_inconnu.py` | EtatInconnu avec etats_possibles |
| `core/gestionnaire_etats.py` | Pathfinding BFS + détection d'état + auto-génération chemins Popup |
| `manoirs/manoir_base.py` | naviguer_vers(), verifier_etat(), _etats_a_tester_apres_reprise |
| `manoirs/instances/manoir_bluestacks.py` | Refactoré pour utiliser le nouveau système |
| `config/etat-chemin.toml` | Configuration des priorités et dossiers |
| `actions/item.py` | Classe Item + helpers de conditions |

---

## Référence - États créés

Dossier : `manoirs/etats/`

| État | Fichier | Type | Détection |
|------|---------|------|-----------|
| non_lance | etat_non_lance.py | Etat | Fenêtre BlueStacks absente |
| chargement | etat_chargement.py | Etat | Fenêtre présente + _lancement_initie + pas icone_jeu_charge |
| ville | etat_ville.py | Etat | icone_jeu_charge.png visible |
| popup_rapport | etat_popup_rapport.py | Popup | popups/rapport_developpement.png visible |
| popup_connexion | etat_popup_connexion.py | Popup | popups/connexion_quotidienne.png visible |
| popup_gratuit | etat_popup_gratuit.py | Popup | boutons/bouton_gratuit.png visible |

---

## Référence - Chemins créés

Dossier : `manoirs/chemins/`

| Chemin | Initial → Sortie | Actions |
|--------|------------------|---------|
| chemin_lancer_bluestacks | non_lance → chargement | ActionLancerRaccourci, set _lancement_initie=True |
| chemin_attendre_chargement | chargement → EtatInconnu[ville, popups] | ActionAttendre(5s), ActionReprisePreparerTour |

### Chemins auto-générés (Popup)

Les chemins pour les popups sont générés automatiquement par `GestionnaireEtats` à partir des classes `Popup` :

| Popup | Initial → Sortie | Fermeture |
|-------|------------------|-----------|
| popup_rapport | popup_rapport → EtatInconnu | Clic positionnel (50, 50) relatif |
| popup_connexion | popup_connexion → EtatInconnu | ActionBouton sur image de détection |
| popup_gratuit | popup_gratuit → EtatInconnu | ActionBouton sur bouton gratuit |

---

## Flux de navigation

```
non_lance ──[lancer_bluestacks]──► chargement
                                       │
                    ┌──────────────────┴──────────────────┐
                    │                                     │
                    ▼                                     ▼
            [attendre_chargement]                    (timeout)
                    │                                     │
        ┌───────────┼───────────┐                         ▼
        ▼           ▼           ▼                      BLOQUE
   popup_*       popup_*      ville
        │           │           │
        └───────────┴───────────┘
                    │
         [fermer_popup_*] (cycle jusqu'à ville)
                    │
                    ▼
                  ville ══► PRET ══► gestion_tour()
```

---

## Mécanisme clé : etats_possibles

Après un chemin incertain (EtatInconnu), seuls les `etats_possibles` sont testés :

```python
# Dans chemin_attendre_chargement.py
etat_sortie = EtatInconnu(
    etats_possibles=["ville", "popup_rapport", "popup_connexion", "popup_gratuit"]
)

# Après ActionReprisePreparerTour, seuls ces 4 états sont testés
# (pas non_lance, pas chargement, etc.)
```
