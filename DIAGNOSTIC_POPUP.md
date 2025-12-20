# Diagnostic: Popup Connexion Quotidienne non détecté

## Problème
Le popup "Connexion Quotidienne" n'était pas détecté malgré sa présence visible à l'écran.

## Analyse

### Template matching
- **Template**: `templates/popups/connexion_quotidienne.png` (280x40 pixels)
- **Capture d'écran**: 565x1041 pixels
- **Score de correspondance**: **0.6264**
- **Position détectée**: (140, 176)

### Tests de seuils
| Seuil | Résultat | Note |
|-------|----------|------|
| 0.50  | ✓ DÉTECTÉ | |
| 0.60  | ✓ DÉTECTÉ | |
| **0.70** | ✗ **NON DÉTECTÉ** | **← Seuil configuré** |
| 0.80  | ✗ NON DÉTECTÉ | |
| 0.90  | ✗ NON DÉTECTÉ | |

## Cause racine

Le seuil de détection était trop élevé : **0.7**
Le score réel du popup est : **0.6264**

**0.6264 < 0.7** → Popup NON détecté

## Solution appliquée

Fichier modifié : `actions/popups/action_collecter_connexion_quotidienne.py:18`

**Avant:**
```python
def __init__(self, manoir, threshold_popup=0.7, threshold_bouton=0.6):
```

**Après:**
```python
def __init__(self, manoir, threshold_popup=0.6, threshold_bouton=0.6):
```

## Pourquoi le score est-il de 0.63 seulement ?

Possibles raisons :
1. **Résolution différente** : Le template a été extrait à une résolution différente
2. **Antialiasing** : Différences de rendu du texte
3. **Compression** : Artefacts de compression JPEG/PNG
4. **Couleurs** : Légères variations de couleur

## Recommandation

Pour améliorer la détection :
1. **Option A** : Garder le seuil à 0.6 (solution actuelle)
2. **Option B** : Re-extraire le template depuis une vraie capture d'écran récente
   - Faire une capture du popup
   - Extraire exactement la zone du popup
   - Remplacer `templates/popups/connexion_quotidienne.png`
   - Cela devrait donner un score > 0.9

## Vérification

Image de résultat sauvegardée dans : `debug_detection_result.png`

Cette image montre le rectangle vert autour du popup détecté avec le score de 0.626.
