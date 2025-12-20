# Fix : Popups non détectés au démarrage

## Problème

Lorsque le jeu est déjà chargé au démarrage (redémarrage du script), les popups présents à l'écran n'étaient **pas détectés**.

### Scénario
1. BlueStacks déjà ouvert avec le jeu chargé
2. Script démarre
3. `ActionVerifierPretRapide` détecte `icone_jeu_charge.png`
4. Le manoir passe en état PRÊT
5. La séquence de lancement est **cleared** (ligne 76)
6. ❌ Les popups ne sont **jamais vérifiés**

### Logs observés
```
14:18:42 - INFO - ActionVerifierPretRapide - Manoir Principal: Jeu DÉJÀ PRÊT détecté
14:18:42 - INFO - Manoir Principal - LANCEMENT -> PRET
14:18:42 - INFO - Manoir Principal - Jeu chargé et prêt !
```

Mais le popup "Connexion Quotidienne" était visible sur la capture d'écran !

## Solution

**Fichier modifié** : `actions/bluestacks/action_verifier_pret_rapide.py`

### Changements

#### 1. Vérification des popups AVANT de signaler PRÊT

**Avant :**
```python
if icone_presente:
    self.logger.info("Jeu DÉJÀ PRÊT détecté - skip attente")
    self.fenetre.signaler_jeu_charge()
    self.fenetre.sequence.clear()  # ← Popups jamais vérifiés !
```

**Après :**
```python
if icone_presente:
    self.logger.info("Jeu DÉJÀ PRÊT détecté - vérification des popups")

    # AVANT de signaler PRÊT, gérer les popups
    popups_detectes = self._gerer_popups_demarrage()

    if popups_detectes:
        self.logger.info(f"{popups_detectes} popup(s) traité(s)")

    self.fenetre.signaler_jeu_charge()
    self.fenetre.sequence.clear()
```

#### 2. Nouvelle méthode : `_gerer_popups_demarrage()`

Gère automatiquement les popups courants de démarrage :

1. **Connexion quotidienne** (threshold=0.6)
   - Cherche le bouton "Collecter"
   - Clique sur le bouton ou position estimée (85% hauteur)

2. **Rapport de développement** (threshold=0.7)
   - Clique sur la croix (95% largeur, 5% hauteur)

3. **Bouton gratuit** (threshold=0.7)
   - Cherche et clique sur le bouton

**Boucle intelligente** :
- Maximum 3 popups à la suite
- Arrêt automatique si aucun popup trouvé
- Re-capture entre chaque popup

### Code de la méthode

```python
def _gerer_popups_demarrage(self):
    """Gère les popups courants de démarrage

    Returns:
        int: Nombre de popups détectés et traités
    """
    import time

    popups_traites = 0
    max_tentatives = 3

    for _ in range(max_tentatives):
        popup_trouve = False

        # Vérifier Connexion quotidienne
        if self.fenetre.detect_image("popups/connexion_quotidienne.png", threshold=0.6):
            # Cliquer sur Collecter
            ...
            popups_traites += 1
            popup_trouve = True

        # Vérifier Rapport développement
        elif self.fenetre.detect_image("popups/rapport_developpement.png", threshold=0.7):
            # Cliquer sur croix
            ...
            popups_traites += 1
            popup_trouve = True

        # Vérifier Bouton gratuit
        elif self.fenetre.detect_image("boutons/bouton_gratuit.png", threshold=0.7):
            # Cliquer dessus
            ...
            popups_traites += 1
            popup_trouve = True

        if not popup_trouve:
            break

        self.fenetre.capture(force=True)

    return popups_traites
```

## Nouveaux logs attendus

```
14:18:42 - INFO - ActionVerifierPretRapide - Manoir Principal: Jeu DÉJÀ PRÊT détecté - vérification des popups de démarrage
14:18:42 - INFO - ActionVerifierPretRapide - Manoir Principal: Popup 'Connexion Quotidienne' détecté
14:18:44 - INFO - ActionVerifierPretRapide - Manoir Principal: 1 popup(s) traité(s)
14:18:44 - INFO - Manoir Principal - LANCEMENT -> PRET
14:18:44 - INFO - Manoir Principal - Jeu chargé et prêt !
```

## Avantages

1. ✅ **Popups détectés au démarrage** même si jeu déjà chargé
2. ✅ **Pas de duplication** : Si déjà géré, la boucle normale ne les re-détecte pas
3. ✅ **Gestion multiple** : Jusqu'à 3 popups consécutifs
4. ✅ **Performance** : Arrêt dès qu'aucun popup n'est trouvé
5. ✅ **Robuste** : Utilise les mêmes seuils que les actions dédiées

## Cas d'usage

### Cas 1 : Démarrage à froid
BlueStacks pas encore lancé → Séquence de lancement normale → Popups détectés dans la boucle `ActionWhile`

### Cas 2 : Démarrage à chaud (FIX)
BlueStacks déjà ouvert → `ActionVerifierPretRapide` détecte le jeu chargé → **Gère les popups avant de passer en PRÊT** → Aucun popup manqué

## Notes techniques

- Les seuils utilisés sont les mêmes que dans les actions dédiées
- Le délai entre chaque popup est de 1.5s (temps pour l'animation)
- Maximum 3 popups gérés (évite boucle infinie si détection erronée)
- Force la re-capture entre chaque popup pour détecter le suivant

## Tests recommandés

1. Démarrer avec BlueStacks fermé → Vérifier que les popups sont détectés normalement
2. Démarrer avec BlueStacks ouvert + popups visibles → Vérifier qu'ils sont détectés et fermés
3. Démarrer avec BlueStacks ouvert + aucun popup → Vérifier que ça passe en PRÊT directement
