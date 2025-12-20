# -*- coding: utf-8 -*-
"""Script pour extraire l'icône du jeu chargé"""
from PIL import Image
import os
import glob

# Trouver le fichier Capture
template_dir = r"C:\Projets\2 project\templates"
pattern = os.path.join(template_dir, "Capture*.png")
captures = glob.glob(pattern)

if not captures:
    print("ERREUR: Aucun fichier Capture*.png trouve")
    exit(1)

capture_path = captures[0]
print(f"Fichier trouve: {capture_path}")

# Ouvrir l'image
img = Image.open(capture_path)
print(f"Dimensions de la capture: {img.size}")

# L'icône de la carte avec le flingue est en bas à gauche
# Coordonnées ajustées pour capturer uniquement l'icône
# Format: (left, top, right, bottom)
left = 8
top = img.size[1] - 78  # Ajusté pour capturer l'icône
right = 72
bottom = img.size[1] - 14  # Ajusté

print(f"Zone d'extraction: left={left}, top={top}, right={right}, bottom={bottom}")

# Extraire l'icône
icon = img.crop((left, top, right, bottom))
print(f"Dimensions de l'icone extraite: {icon.size}")

# Sauvegarder dans les deux emplacements
output_paths = [
    r"C:\Projets\2 project\templates\icone_jeu_charge.png",
    r"C:\Projets\2 project\templates\ville\icone_jeu_charge.png"
]

for output_path in output_paths:
    icon.save(output_path)
    print(f"OK - Icone sauvegardee: {output_path}")

print("\nTermine !")
