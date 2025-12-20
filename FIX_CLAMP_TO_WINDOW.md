# Fix : Erreur clamp_to_window()

## Erreur

```
ERROR - Engine - Erreur exécution action: clamp_to_window() takes 3 positional arguments but 4 were given
```

## Cause

**Fichier** : `manoirs/manoir_base.py:661`

### Signature de la fonction

```python
def clamp_to_window(x, y, window_rect):
    """Contraint un point à rester dans les limites de la fenêtre

    Args:
        x, y: Coordonnées du point
        window_rect: Tuple (left, top, right, bottom)  ← UN SEUL paramètre tuple
    """
```

### Appel incorrect

**Avant :**
```python
x, y = clamp_to_window(x, y, self.largeur, self.hauteur)
                                ^^^^^^^^^^^^^^^^^^^^^^^^
                                4 arguments au lieu de 3
```

La fonction était appelée avec 4 arguments :
1. `x`
2. `y`
3. `self.largeur`
4. `self.hauteur`

Mais elle attend seulement 3 arguments :
1. `x`
2. `y`
3. `window_rect` (un tuple)

## Solution

**Fichier modifié** : `manoirs/manoir_base.py:661`

**Après :**
```python
# Contraindre aux limites (window_rect = (0, 0, largeur, hauteur))
window_rect = (0, 0, self.largeur, self.hauteur)
x, y = clamp_to_window(x, y, window_rect)
```

Maintenant on passe un **tuple** `(0, 0, largeur, hauteur)` qui représente :
- `left = 0`
- `top = 0`
- `right = largeur`
- `bottom = hauteur`

## Contexte

Cette erreur se produisait dans la méthode `click_at()` quand on essayait de :
1. Convertir des coordonnées relatives en absolues
2. **Contraindre** le point aux limites de la fenêtre
3. Convertir en coordonnées écran
4. Effectuer le clic

L'étape 2 échouait à cause de l'appel incorrect.

## Impact

Cette erreur bloquait **tous les clics** qui tentaient de contraindre les coordonnées aux limites de la fenêtre, notamment :
- Fermeture de popups
- Clics sur boutons
- Toute action `click_at()`

## Test

Pour vérifier que c'est corrigé, essayez de fermer un popup. Le clic devrait maintenant fonctionner sans erreur.
