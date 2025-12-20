# Fix : Replacement automatique de la fenêtre

## Problème

Quand le jeu est en état PRÊT et que l'utilisateur déplace ou redimensionne manuellement la fenêtre, celle-ci **ne se replace pas automatiquement** lors du prochain tour.

### Comportement observé

1. Le jeu est en état PRÊT
2. L'utilisateur déplace la fenêtre manuellement
3. Le manoir reprend la main au tour suivant
4. ❌ La fenêtre reste à la position déplacée (pas de replacement)

### Cause

`placer_fenetre()` n'était appelée que pendant la **phase de lancement** :
- Dans `ActionVerifierPretRapide` (ligne 123)
- Dans `ActionVerifierPret` (ligne 58)

Une fois en état PRÊT, `placer_fenetre()` n'était **plus jamais appelée**.

## Solution

**Fichier modifié** : `manoirs/manoir_base.py:155`

### Modification de `activate()`

Ajout de la vérification et du replacement dans la méthode `activate()` qui est appelée **à chaque tour** :

**Avant :**
```python
def activate(self):
    """Active la fenêtre (met au premier plan)"""
    if not self._hwnd:
        self.find_window()

    if self._hwnd:
        return self._wm.activate_window(self._hwnd)

    return False
```

**Après :**
```python
def activate(self):
    """Active la fenêtre (met au premier plan)

    Vérifie aussi si la fenêtre a été déplacée/redimensionnée et la replace si nécessaire.
    """
    if not self._hwnd:
        self.find_window()

    if self._hwnd:
        # Vérifier et replacer la fenêtre si elle a été déplacée/redimensionnée
        if self.position_x is not None or self.position_y is not None:
            self.placer_fenetre()

        return self._wm.activate_window(self._hwnd)

    return False
```

## Fonctionnement

### À chaque tour

1. **`activate()` est appelée** (ligne 166)
2. **`placer_fenetre()` est appelée** (ligne 169) SI une position est configurée
3. **`placer_fenetre()` vérifie** si la fenêtre a bougé (avec tolérance de 5px)
4. **Replacement automatique** si déplacement détecté

### Détection intelligente (dans `placer_fenetre()`)

Rappel de la logique déjà implémentée :

```python
# Comparer position actuelle vs position attendue
if abs(x_actuel - x_attendu) <= 5 and [...]:
    # Fenêtre n'a pas bougé, pas besoin de replacer
    return True
else:
    # Fenêtre modifiée, replacer !
    self.logger.info("Fenêtre déplacée/redimensionnée détectée")
    # ... replacement ...
```

### Tolérance de 5px

Pour éviter les replacements inutiles dus aux bordures Windows.

## Logs attendus

### Cas 1 : Fenêtre à la bonne place (majoritaire)

```
(pas de log - return immédiat dans placer_fenetre)
```

### Cas 2 : Fenêtre déplacée

```
INFO - Manoir Principal: Fenêtre déplacée/redimensionnée détectée:
       position actuelle (250, 150, 728x1040) != position attendue (-128, 0, 728x1040)
INFO - Manoir Principal: Largeur calculée (728px) > largeur config (600px).
       Décalage de 128px vers la gauche (x: 0 -> -128)
```

## Condition de replacement

Le replacement ne se fait **QUE SI** :
- `position_x` ou `position_y` est configuré (pas None)
- ET la fenêtre a été effectivement déplacée/redimensionnée

Si `position_x` et `position_y` sont tous deux `None`, le replacement **n'est pas effectué** (fenêtre libre).

## Avantages

1. ✅ **Replacement automatique** à chaque tour
2. ✅ **Performance optimale** : Pas de replacement si fenêtre inchangée (tolérance 5px)
3. ✅ **Ratio maintenu** : La largeur est recalculée selon le ratio
4. ✅ **Ajustement intelligent** : Décalage vers la gauche si largeur > config

## Désactiver le replacement

Si vous ne voulez **pas** de replacement automatique, configurez :

```python
"principal": {
    ...
    "position_x": None,  # Pas de contrainte X
    "position_y": None,  # Pas de contrainte Y
}
```

Avec cette configuration, la fenêtre reste où l'utilisateur la place.

## Impact sur les performances

**Minimal** car :
- `placer_fenetre()` fait un return immédiat si fenêtre inchangée
- Vérification simple de coordonnées (< 1ms)
- Pas de redimensionnement si pas nécessaire

## Tests recommandés

1. **Fenêtre à la bonne place** → Vérifier qu'il n'y a pas de log (pas de replacement)
2. **Déplacer manuellement la fenêtre** → Vérifier qu'elle se replace au prochain tour
3. **Redimensionner la fenêtre** → Vérifier qu'elle se redimensionne et replace
4. **position_x/y = None** → Vérifier qu'il n'y a pas de replacement
