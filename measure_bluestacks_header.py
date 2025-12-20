# -*- coding: utf-8 -*-
"""Script pour mesurer le bandeau supérieur BlueStacks

Capture une fenêtre BlueStacks et affiche les dimensions pour
permettre de mesurer manuellement le bandeau supérieur.
"""

import win32gui
from PIL import ImageGrab


def find_bluestacks_window(titre_partiel):
    """Trouve une fenêtre BlueStacks"""
    found = []

    def callback(hwnd, results):
        if win32gui.IsWindowVisible(hwnd):
            titre = win32gui.GetWindowText(hwnd)
            if titre and titre_partiel.lower() in titre.lower():
                results.append((hwnd, titre))

    win32gui.EnumWindows(callback, found)
    return found[0] if found else (None, None)


def main():
    print("=" * 60)
    print("MESURE DU BANDEAU SUPÉRIEUR BLUESTACKS")
    print("=" * 60)

    # Chercher une fenêtre BlueStacks
    for titre in ["farm1", "principal", "bluestacks"]:
        hwnd, nom = find_bluestacks_window(titre)
        if hwnd:
            break

    if not hwnd:
        print("Aucune fenêtre BlueStacks trouvée!")
        return

    print(f"\nFenêtre trouvée: {nom}")

    # Obtenir les dimensions
    rect = win32gui.GetWindowRect(hwnd)
    left, top, right, bottom = rect
    width = right - left
    height = bottom - top

    print(f"Position: ({left}, {top})")
    print(f"Dimensions: {width} x {height}")

    # Capturer la fenêtre
    print("\nCapture de la fenêtre...")
    screenshot = ImageGrab.grab(bbox=rect)

    # Sauvegarder pour analyse manuelle
    output_path = "bluestacks_capture.png"
    screenshot.save(output_path)
    print(f"Capture sauvegardée: {output_path}")

    # Analyser les pixels pour trouver le changement de couleur
    # Le bandeau supérieur est généralement plus sombre/coloré
    print("\n--- Analyse des pixels (colonne centrale) ---")
    center_x = width // 2

    print(f"\nCouleurs des 100 premiers pixels (x={center_x}):")
    print("Y    | RGB")
    print("-" * 30)

    prev_color = None
    transitions = []

    for y in range(min(150, height)):
        color = screenshot.getpixel((center_x, y))

        # Détecter les transitions de couleur significatives
        if prev_color:
            diff = sum(abs(c1 - c2) for c1, c2 in zip(color[:3], prev_color[:3]))
            if diff > 50:  # Transition significative
                transitions.append((y, prev_color, color))

        if y < 100 or (prev_color and sum(abs(c1 - c2) for c1, c2 in zip(color[:3], prev_color[:3])) > 30):
            print(f"{y:4} | {color[:3]}")

        prev_color = color

    print("\n--- Transitions détectées ---")
    for y, before, after in transitions[:5]:
        print(f"Y={y}: {before[:3]} -> {after[:3]}")

    if transitions:
        # La première grande transition est probablement la fin du bandeau
        premiere_transition = transitions[0][0]
        print(f"\n>>> BANDEAU SUPÉRIEUR ESTIMÉ: ~{premiere_transition} pixels <<<")

    print("\n" + "=" * 60)
    print("Ouvre 'bluestacks_capture.png' et mesure manuellement")
    print("la hauteur du bandeau supérieur (barre titre + navigation)")
    print("=" * 60)

    input("\nAppuyez sur Entrée pour quitter...")


if __name__ == "__main__":
    main()
