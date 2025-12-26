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

## 2. Refactorer les chemins pour utiliser `ActionBouton`

Les chemins actuels utilisent `ActionSimple` avec des lambdas. Remplacer par `ActionBouton` :

- [ ] `manoirs/chemins/chemin_fermer_popup_rapport.py`
  - Actuellement : ActionSimple avec click_at(50, 50)
  - À faire : Définir comment fermer ce popup (clic hors zone ? bouton X ?)

- [ ] `manoirs/chemins/chemin_fermer_popup_connexion.py`
  - Actuellement : ActionSimple avec click_image("popups/connexion_quotidienne.png")
  - À faire : ActionBouton(manoir, "popups/connexion_quotidienne.png")

- [ ] `manoirs/chemins/chemin_fermer_popup_gratuit.py`
  - Actuellement : ActionSimple avec click_image("boutons/bouton_gratuit.png")
  - À faire : ActionBouton(manoir, "boutons/bouton_gratuit.png")

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

## 6. Modifier ManoirBase pour gérer `etat_requis`

- [ ] Ajouter méthode `ajouter_action_longue(action_longue)` dans `ManoirBase`
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

## Référence - Fichiers clés

| Fichier | Rôle |
|---------|------|
| `core/etat.py` | Classe de base Etat avec verif(manoir) |
| `core/chemin.py` | Classe de base Chemin avec fonction_actions(manoir) |
| `core/etat_inconnu.py` | EtatInconnu avec etats_possibles |
| `core/gestionnaire_etats.py` | Pathfinding BFS + détection d'état |
| `manoirs/manoir_base.py` | naviguer_vers(), verifier_etat(), _etats_a_tester_apres_reprise |
| `manoirs/instances/manoir_bluestacks.py` | Refactoré pour utiliser le nouveau système |
| `config/etat-chemin.toml` | Configuration des priorités et dossiers |
| `actions/item.py` | Classe Item + helpers de conditions |

---

## Référence - États créés

Dossier : `manoirs/etats/`

| État | Fichier | Détection |
|------|---------|-----------|
| non_lance | etat_non_lance.py | Fenêtre BlueStacks absente |
| chargement | etat_chargement.py | Fenêtre présente + _lancement_initie + pas icone_jeu_charge |
| ville | etat_ville.py | icone_jeu_charge.png visible |
| popup_rapport | etat_popup_rapport.py | popups/rapport_developpement.png visible |
| popup_connexion | etat_popup_connexion.py | popups/connexion_quotidienne.png visible |
| popup_gratuit | etat_popup_gratuit.py | boutons/bouton_gratuit.png visible |

---

## Référence - Chemins créés

Dossier : `manoirs/chemins/`

| Chemin | Initial → Sortie | Actions |
|--------|------------------|---------|
| chemin_lancer_bluestacks | non_lance → chargement | ActionLancerRaccourci, set _lancement_initie=True |
| chemin_attendre_chargement | chargement → EtatInconnu[ville, popups] | ActionAttendre(5s), ActionReprisePreparerTour |
| chemin_fermer_popup_rapport | popup_rapport → EtatInconnu | Clic pour fermer |
| chemin_fermer_popup_connexion | popup_connexion → EtatInconnu | Clic sur popup |
| chemin_fermer_popup_gratuit | popup_gratuit → EtatInconnu | Clic sur bouton gratuit |

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
