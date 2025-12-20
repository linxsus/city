# Templates - Images de référence pour la détection visuelle

Ce dossier contient les images templates utilisées par le système de vision
pour détecter les éléments du jeu.

## Structure

```
templates/
├── popups/          # Popups d'erreur et d'information
├── boutons/         # Boutons cliquables
├── ville/           # Éléments de la vue ville
├── carte/           # Éléments de la carte du monde
├── mercenaires/     # Éléments liés aux mercenaires
└── evenements/      # Indicateurs d'événements
```

## Comment créer des templates

### 1. Capture d'écran
- Utilisez `fenetre.save_capture()` pour capturer l'écran
- Ou faites une capture manuelle avec Print Screen

### 2. Découpage
- Ouvrez la capture dans un éditeur d'images (Paint, GIMP, Photoshop)
- Découpez uniquement l'élément à détecter
- Gardez une marge minimale autour de l'élément
- Évitez les zones qui changent (textes dynamiques, animations)

### 3. Sauvegarde
- Format: PNG (recommandé) ou JPG
- Nommez de façon descriptive: `bouton_attaquer.png`, `popup_erreur_reseau.png`

### 4. Test
- Utilisez `fenetre.detect_image("templates/xxx.png")` pour tester
- Ajustez le seuil si nécessaire (0.7-0.9)

## Bonnes pratiques

- **Taille**: Templates de 50x50 à 200x200 pixels idéalement
- **Unicité**: L'image doit être unique à l'écran
- **Stabilité**: Évitez les éléments qui changent (compteurs, jauges)
- **Contraste**: Préférez les éléments avec un bon contraste
- **Multiples**: Créez plusieurs versions si l'apparence varie

## Templates requis

### popups/
- `compte_utilise.png` - Popup "Compte utilisé ailleurs"
- `connexion_perdue.png` - Popup "Connexion perdue"
- `erreur_reseau.png` - Popup "Erreur réseau"
- `ressources_insuffisantes.png` - Popup ressources
- `slots_pleins.png` - Popup slots pleins
- `popup_evenement.png` - Popup publicité/événement
- `popup_recompense.png` - Popup récompense

### boutons/
- `bouton_ok.png` - Bouton OK générique
- `bouton_fermer.png` - Bouton X pour fermer
- `bouton_attaquer.png` - Bouton Attaquer
- `bouton_envoyer.png` - Bouton Envoyer
- `bouton_collecter.png` - Bouton Collecter
- `bouton_ville.png` - Bouton retour ville
- `bouton_carte.png` - Bouton carte monde
- `bouton_mercenaires.png` - Bouton menu mercenaires
- `bouton_recompenses.png` - Bouton récompenses
- `bouton_plus_tard.png` - Bouton "Plus tard"
- `bouton_reconnexion.png` - Bouton reconnexion

### ville/
- `indicateur_ville.png` - Élément indiquant qu'on est en ville
- `ressource_or.png` - Icône ressource or à collecter
- `ressource_cash.png` - Icône ressource cash
- `ressource_metal.png` - Icône ressource métal
- `ressource_cargo.png` - Icône cargo

### carte/
- `tuile_or.png` - Tuile de ressource or
- `tuile_cash.png` - Tuile de ressource cash
- `tuile_metal.png` - Tuile de ressource métal

### mercenaires/
- `mercenaire_disponible.png` - Mercenaire attaquable

### evenements/
- `kill_event_actif.png` - Indicateur Kill Event en cours
