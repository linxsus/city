# Guide : Détection Multi-Échelle

## Problème résolu

Lorsqu'un template a une résolution différente de l'écran (zoom, DPI différent, etc.), la détection classique échoue ou donne un score faible.

## Solution : Détection multi-échelle

La détection multi-échelle teste le template à **plusieurs tailles** (échelles) pour trouver la meilleure correspondance.

## Utilisation

### Option 1 : Dans ImageMatcher directement

```python
from vision.image_matcher import get_image_matcher

matcher = get_image_matcher()

# Détection multi-échelle
result = matcher.find_template_multiscale(
    screenshot,
    "popups/connexion_quotidienne.png",
    threshold=0.7,
    scales=[0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]  # Optionnel
)

if result:
    x, y, confidence = result
    print(f"Trouvé à ({x}, {y}) avec score {confidence:.2f}")
```

### Option 2 : Dans un Manoir (recommandé)

```python
# Détection simple
if self.detect_image_multiscale("popups/connexion_quotidienne.png", threshold=0.7):
    print("Popup détecté !")

# Trouver la position
position = self.find_image_multiscale("popups/connexion_quotidienne.png", threshold=0.7)
if position:
    x, y = position
    self.click_at(x, y)
```

### Option 3 : Avec des échelles personnalisées

```python
# Pour un template plus petit que prévu
position = self.find_image_multiscale(
    "boutons/petit_bouton.png",
    threshold=0.7,
    scales=[0.5, 0.6, 0.7, 0.8, 0.9, 1.0]  # Chercher à 50%-100%
)

# Pour un template potentiellement plus grand
position = self.find_image_multiscale(
    "boutons/gros_bouton.png",
    threshold=0.7,
    scales=[1.0, 1.2, 1.4, 1.6, 1.8, 2.0]  # Chercher à 100%-200%
)
```

## Échelles par défaut

Si vous ne spécifiez pas `scales`, ces valeurs sont utilisées :
```python
[0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]
```

Cela couvre de **70% à 130%** de la taille originale.

## Performance

⚠️ **La détection multi-échelle est plus lente** car elle teste plusieurs tailles.

**Recommandations :**
- Utilisez-la uniquement pour les templates problématiques
- Limitez le nombre d'échelles (5-7 max)
- Utilisez `detect_image()` classique pour les templates qui fonctionnent bien

## Exemple concret : Popup Connexion Quotidienne

### Avant (échelle unique)
```python
# Score : 0.6264 avec threshold=0.7 → NON DÉTECTÉ
if self.detect_image("popups/connexion_quotidienne.png", threshold=0.7):
    ...
```

### Après (multi-échelle)
```python
# Teste plusieurs échelles → Meilleur score trouvé
if self.detect_image_multiscale("popups/connexion_quotidienne.png", threshold=0.7):
    ...
```

### Résultat du test
- **Échelle 1.0** : Score = 0.6264 ← Meilleur
- Échelle 0.8 : Score = 0.4107
- Échelle 0.7 : Score = 0.3893

Dans ce cas, le template était déjà à la bonne échelle, mais le score restait faible (0.63).

## Diagnostic : Quand l'utiliser ?

### ✓ Utilisez multi-échelle si :
- Le score est faible (< 0.7) à l'échelle normale
- Le template a été extrait d'un écran avec une résolution différente
- Vous voulez supporter plusieurs résolutions d'écran

### ✗ N'utilisez PAS multi-échelle si :
- Le template fonctionne déjà bien (score > 0.8)
- La performance est critique
- Le template est parfaitement à l'échelle

## Optimisation : Re-extraire le template

Pour de meilleures performances, **re-extraire le template** à la bonne résolution :

1. Faire une capture d'écran réelle
2. Extraire exactement la zone voulue
3. Remplacer le template existant

Résultat : Score > 0.9 avec détection simple (pas besoin de multi-échelle).

## API Complète

### ImageMatcher

```python
find_template_multiscale(screenshot, template_path, threshold=None,
                         scales=None, return_scale=False)
```

### ManoirBase

```python
# Détection
detect_image_multiscale(template_path, threshold=None, region=None, scales=None)

# Trouver position
find_image_multiscale(template_path, threshold=None, region=None, scales=None)
```

## Logs

La détection multi-échelle génère des logs détaillés :

```
[DEBUG] Template trouvé (multi-échelle): connexion_quotidienne.png
        à (280, 196) conf=0.63 échelle=1.00
```

ou

```
[DEBUG] Template non trouvé (multi-échelle): connexion_quotidienne.png
        (meilleur score: 0.45 à échelle 0.80)
```
