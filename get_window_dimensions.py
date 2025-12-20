# -*- coding: utf-8 -*-
"""Script pour obtenir les dimensions d'une fenêtre BlueStacks"""

import win32gui


def get_all_windows():
    """Liste toutes les fenêtres visibles avec leurs dimensions"""
    windows = []

    def callback(hwnd, results):
        if win32gui.IsWindowVisible(hwnd):
            titre = win32gui.GetWindowText(hwnd)
            if titre:
                rect = win32gui.GetWindowRect(hwnd)
                left, top, right, bottom = rect
                width = right - left
                height = bottom - top
                ratio = width / height if height > 0 else 0
                results.append({
                    'hwnd': hwnd,
                    'titre': titre,
                    'x': left,
                    'y': top,
                    'largeur': width,
                    'hauteur': height,
                    'ratio': ratio
                })

    win32gui.EnumWindows(callback, windows)
    return windows


def find_bluestacks_windows():
    """Trouve les fenêtres BlueStacks"""
    all_windows = get_all_windows()
    bluestacks = [w for w in all_windows if 'bluestacks' in w['titre'].lower() or 'principal' in w['titre'].lower()]
    return bluestacks


def main():
    print("=" * 70)
    print("DIMENSIONS DES FENÊTRES BLUESTACKS")
    print("=" * 70)

    bluestacks_windows = find_bluestacks_windows()

    if not bluestacks_windows:
        print("\nAucune fenêtre BlueStacks trouvée.")
        print("\nRecherche dans toutes les fenêtres...")
        all_windows = get_all_windows()
        print(f"\nFenêtres disponibles ({len(all_windows)}):\n")
        for w in sorted(all_windows, key=lambda x: x['titre']):
            if len(w['titre']) > 3:  # Ignorer les titres trop courts
                print(f"  - {w['titre'][:50]}")
    else:
        print(f"\nTrouvé {len(bluestacks_windows)} fenêtre(s) BlueStacks:\n")

        for w in bluestacks_windows:
            print(f"Fenêtre: {w['titre']}")
            print(f"  Position:   x={w['x']}, y={w['y']}")
            print(f"  Dimensions: {w['largeur']} x {w['hauteur']}")
            print(f"  Ratio L/H:  {w['ratio']:.4f}")
            print()

            # Comparaison avec ratio cible (sans pub)
            ratio_cible = 600 / 1040
            diff_ratio = abs(w['ratio'] - ratio_cible)

            print(f"  --- Analyse ---")
            print(f"  Ratio cible (sans pub): {ratio_cible:.4f}")
            print(f"  Différence avec cible:  {diff_ratio:.4f}")

            if diff_ratio < 0.02:
                print(f"  Status: ✓ Proche du ratio sans pub")
            else:
                print(f"  Status: ✗ Ratio différent (probablement avec pub)")
                # Calculer quelle serait la hauteur pour atteindre le ratio cible
                hauteur_ideale = w['largeur'] / ratio_cible
                print(f"  Hauteur idéale pour ratio cible: {hauteur_ideale:.0f}px")

            print("-" * 50)

    input("\nAppuyez sur Entrée pour quitter...")


if __name__ == "__main__":
    main()
