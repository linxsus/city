# -*- coding: utf-8 -*-
"""
Test: Redimensionner BlueStacks avec hauteur seule
Voir si BlueStacks ajuste automatiquement sa largeur
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


def get_window_info(hwnd):
    """Récupère les infos d'une fenêtre"""
    rect = win32gui.GetWindowRect(hwnd)
    width = rect[2] - rect[0]
    height = rect[3] - rect[1]
    ratio = width / height if height > 0 else 0
    return {
        'x': rect[0],
        'y': rect[1],
        'width': width,
        'height': height,
        'ratio': ratio
    }


def resize_height_only(hwnd, new_height):
    """Redimensionne uniquement la hauteur"""
    rect = win32gui.GetWindowRect(hwnd)
    x, y = rect[0], rect[1]
    width = rect[2] - rect[0]

    print(f"  Avant: {width} x {rect[3] - rect[1]}")
    print(f"  Commande: MoveWindow avec largeur={width}, hauteur={new_height}")

    win32gui.MoveWindow(hwnd, x, y, width, new_height, True)
    time.sleep(0.3)  # Attendre que BlueStacks s'ajuste

    # Récupérer les nouvelles dimensions
    new_rect = win32gui.GetWindowRect(hwnd)
    new_width = new_rect[2] - new_rect[0]
    new_height_actual = new_rect[3] - new_rect[1]

    print(f"  Après: {new_width} x {new_height_actual}")

    if new_width != width:
        print(f"  ✓ BlueStacks a ajusté la largeur: {width} -> {new_width}")
    else:
        print(f"  ✗ Largeur inchangée")

    return new_width, new_height_actual


def main():
    print("=" * 60)
    print("TEST: Redimensionnement hauteur seule")
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

    # Info initiale
    info = get_window_info(hwnd)
    print(f"\nDimensions actuelles:")
    print(f"  Position: ({info['x']}, {info['y']})")
    print(f"  Taille: {info['width']} x {info['height']}")
    print(f"  Ratio: {info['ratio']:.4f}")

    # Test 1: Augmenter la hauteur
    print("\n--- Test 1: Augmenter hauteur de 100px ---")
    new_h = info['height'] + 100
    resize_height_only(hwnd, new_h)

    time.sleep(0.5)

    # Test 2: Revenir à la hauteur initiale
    print("\n--- Test 2: Revenir à hauteur initiale ---")
    resize_height_only(hwnd, info['height'])

    time.sleep(0.5)

    # Test 3: Réduire la hauteur
    print("\n--- Test 3: Réduire hauteur de 100px ---")
    new_h = info['height'] - 100
    resize_height_only(hwnd, new_h)

    time.sleep(0.5)

    # Test 4: Hauteur cible 1040
    print("\n--- Test 4: Hauteur cible = 1040 ---")
    resize_height_only(hwnd, 1040)

    # Résultat final
    time.sleep(0.5)
    final = get_window_info(hwnd)

    print("\n" + "=" * 60)
    print("RÉSULTAT FINAL")
    print("=" * 60)
    print(f"  Taille: {final['width']} x {final['height']}")
    print(f"  Ratio: {final['ratio']:.4f}")

    # Conclusion
    print("\n" + "=" * 60)
    print("CONCLUSION")
    print("=" * 60)

    if final['width'] != info['width']:
        print("""
✓ BlueStacks AJUSTE automatiquement sa largeur!
  -> On peut utiliser resize_height_only() pour le redimensionnement
""")
    else:
        print("""
✗ BlueStacks ne modifie PAS la largeur automatiquement
  -> Il faut continuer à utiliser le ratio pour calculer la largeur
""")

    input("\nAppuyez sur Entrée pour quitter...")


if __name__ == "__main__":
    main()
