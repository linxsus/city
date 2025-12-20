# Templates Ville

## icone_jeu_charge.png

Cette icône est utilisée pour détecter que le jeu Mafia City est bien chargé sur l'écran principal (la ville).

### Modification lors d'événements

L'icône peut changer lors d'événements spéciaux du jeu. Pour la mettre à jour :

1. Faire une capture d'écran du jeu avec la nouvelle icône
2. Découper l'icône (environ 90x70 pixels)
3. Remplacer ce fichier `icone_jeu_charge.png`

### Conseils

- Capturer l'icône quand elle est bien visible (pas en animation)
- Garder une taille similaire (~90x70 pixels)
- Si l'ancienne icône fonctionnait bien, la sauvegarder avant de la remplacer :
  ```
  icone_jeu_charge.png → icone_jeu_charge_backup.png
  ```

### Icônes alternatives

Si plusieurs icônes sont possibles selon les événements, vous pouvez les ajouter toutes dans la liste `TEMPLATES_JEU_CHARGE` du fichier `fenetres/instances/actions_reelle.py`.
