# -*- coding: utf-8 -*-
"""
Test: Trouver le bon ratio pour BlueStacks sans déformation
"""

import win32gui
import time


def find_bluestacks(titre_partiel):
    """Trouve une fenêtre BlueStacks"""
    found = []

    def callback(hwnd, results):
        if win32gui.IsWindowVisible(hwnd):
            titre = win32gui.GetWindowText(hwnd)
            if titre and titre_partiel.lower() in titre.lower():
                results.append((hwnd, titre))

    win32gui.EnumWindows(callback, found)
    return found[0] if found else (None, None)


def resize_window(hwnd, width, height, x=None, y=None):
    """Redimensionne la fenêtre"""
    rect = win32gui.GetWindowRect(hwnd)
    new_x = x if x is not None else rect[0]
    new_y = y if y is not None else rect[1]

    win32gui.MoveWindow(hwnd, new_x, new_y, width, height, True)
    time.sleep(0.2)

    # Récupérer dimensions réelles
    new_rect = win32gui.GetWindowRect(hwnd)
    actual_w = new_rect[2] - new_rect[0]
    actual_h = new_rect[3] - new_rect[1]

    return actual_w, actual_h


def main():
    print("=" * 60)
    print("TEST: Trouver le bon ratio BlueStacks")
    print("=" * 60)

    # Chercher BlueStacks
    for titre in ["farm1", "principal", "bluestacks"]:
        hwnd, nom = find_bluestacks(titre)
        if hwnd:
            break

    if not hwnd:
        print("Aucune fenêtre BlueStacks trouvée!")
        return

    print(f"\nFenêtre: {nom}")

    # Hauteur cible
    hauteur_cible = 1040

    # Différents ratios à tester
    ratios_test = [
        (0.5769, "600/1040 (config actuelle)"),
        (0.6744, "Zone de jeu calculée (solve_bandeaux)"),
        (0.7316, "Ratio obtenu par resize_height_only"),
        (0.5455, "Sans pub, sans bandeau (563/1032)"),
        (0.5766, "Sans pub, avec bandeau (595/1032)"),
        (0.8556, "Avec pub, sans bandeau (883/1032)"),
        (0.8866, "Avec pub, avec bandeau (915/1032)"),
    ]

    print(f"\nHauteur cible: {hauteur_cible}")
    print("\n" + "=" * 60)
    print("Test de différents ratios - REGARDEZ si l'image est déformée")
    print("=" * 60)

    for ratio, description in ratios_test:
        largeur = int(hauteur_cible * ratio)

        print(f"\n--- Ratio {ratio:.4f}: {description} ---")
        print(f"  Dimensions demandées: {largeur} x {hauteur_cible}")

        actual_w, actual_h = resize_window(hwnd, largeur, hauteur_cible)
        actual_ratio = actual_w / actual_h if actual_h > 0 else 0

        print(f"  Dimensions obtenues:  {actual_w} x {actual_h}")
        print(f"  Ratio obtenu: {actual_ratio:.4f}")

        if actual_w != largeur or actual_h != hauteur_cible:
            print(f"  ⚠️  BlueStacks a modifié les dimensions!")

        input("  >> Appuyez sur Entrée pour tester le ratio suivant...")

    print("\n" + "=" * 60)
    print("QUEL RATIO DONNE UNE IMAGE NON DÉFORMÉE ?")
    print("=" * 60)
    print("""
Notez le ratio qui affiche l'image correctement (non déformée).
Ce ratio sera utilisé dans la configuration.
""")

    # Permettre un test manuel
    while True:
        try:
            ratio_manuel = input("\nEntrez un ratio à tester (ou 'q' pour quitter): ")
            if ratio_manuel.lower() == 'q':
                break

            ratio = float(ratio_manuel)
            largeur = int(hauteur_cible * ratio)

            print(f"  Test: {largeur} x {hauteur_cible} (ratio {ratio})")
            actual_w, actual_h = resize_window(hwnd, largeur, hauteur_cible)
            print(f"  Obtenu: {actual_w} x {actual_h}")

        except ValueError:
            print("  Valeur invalide, entrez un nombre décimal (ex: 0.65)")


if __name__ == "__main__":
    main()
