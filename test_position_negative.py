# -*- coding: utf-8 -*-
"""Test des positions negatives dans Windows"""

from core.window_manager import get_window_manager
import time

def test_position_negative():
    """Test si Windows accepte des coordonnees negatives"""

    wm = get_window_manager()

    # Chercher une fenetre de test
    print("Recherche d'une fenetre...")
    hwnd = wm.find_window("Claude")

    if not hwnd:
        print("Aucune fenetre trouvee")
        return

    titre = wm.get_window_title(hwnd)
    print(f"Fenetre trouvee: {titre}")

    # Position actuelle
    rect = wm.get_window_rect(hwnd)
    print(f"\nPosition actuelle: x={rect[0]}, y={rect[1]}")

    # Test 1: Position negative en X
    print("\n--- Test 1: Position X negative ---")
    success = wm.move_and_resize_window(hwnd, x=-100, y=100)
    if success:
        time.sleep(0.5)
        new_rect = wm.get_window_rect(hwnd)
        print(f"Nouvelle position: x={new_rect[0]}, y={new_rect[1]}")
        print(f"Resultat: {'ACCEPTE' if new_rect[0] < 0 else 'REFUSE (ramene a 0 ou clip)'}")

    time.sleep(1)

    # Test 2: Position negative en Y
    print("\n--- Test 2: Position Y negative ---")
    success = wm.move_and_resize_window(hwnd, x=100, y=-50)
    if success:
        time.sleep(0.5)
        new_rect = wm.get_window_rect(hwnd)
        print(f"Nouvelle position: x={new_rect[0]}, y={new_rect[1]}")
        print(f"Resultat: {'ACCEPTE' if new_rect[1] < 0 else 'REFUSE (ramene a 0 ou clip)'}")

    time.sleep(1)

    # Restaurer position initiale
    print(f"\n--- Restauration position initiale ---")
    wm.move_and_resize_window(hwnd, x=rect[0], y=rect[1])
    print(f"Position restauree: x={rect[0]}, y={rect[1]}")

    print("\n=== CONCLUSION ===")
    print("Les positions negatives permettent de placer une fenetre")
    print("partiellement hors de l'ecran (par exemple pour cacher")
    print("la partie gauche en mettant x negatif).")

if __name__ == "__main__":
    test_position_negative()
