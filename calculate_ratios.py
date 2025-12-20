# -*- coding: utf-8 -*-
"""Script pour calculer les ratios des fenêtres BlueStacks en tenant compte des bandeaux"""

import win32gui

# Constante pour le bandeau supérieur (à ajuster après mesure)
BANDEAU_SUPERIEUR = 32  # Estimation initiale


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
                results.append({
                    'hwnd': hwnd,
                    'titre': titre,
                    'x': left,
                    'y': top,
                    'largeur': width,
                    'hauteur': height,
                })

    win32gui.EnumWindows(callback, windows)
    return windows


def find_bluestacks_windows():
    """Trouve les fenêtres BlueStacks"""
    all_windows = get_all_windows()
    keywords = ['bluestacks', 'principal', 'farm']
    bluestacks = [
        w for w in all_windows
        if any(k in w['titre'].lower() for k in keywords)
    ]
    return bluestacks


def main():
    print("=" * 80)
    print("CALCUL DES RATIOS BLUESTACKS (avec correction bandeau)")
    print("=" * 80)
    print(f"\nBandeau supérieur estimé: {BANDEAU_SUPERIEUR}px")
    print("Bandeau droit estimé: 32px")

    bluestacks_windows = find_bluestacks_windows()

    if not bluestacks_windows:
        print("\nAucune fenêtre BlueStacks trouvée.")
        input("\nAppuyez sur Entrée pour quitter...")
        return

    print(f"\nTrouvé {len(bluestacks_windows)} fenêtre(s):\n")

    # En-tête du tableau
    print("-" * 80)
    print(f"{'Fenêtre':<20} {'Dimensions':<15} {'Ratio brut':<12} {'Ratio 1':<12} {'Ratio 2':<12}")
    print(f"{'':20} {'':15} {'L/H':<12} {'L/(H-32)':<12} {'(L-32)/(H-32)':<12}")
    print("-" * 80)

    for w in bluestacks_windows:
        L = w['largeur']
        H = w['hauteur']

        # Ratio brut (sans correction)
        ratio_brut = L / H if H > 0 else 0

        # Ratio 1: largeur / (hauteur - bandeau_sup)
        H_corrige = H - BANDEAU_SUPERIEUR
        ratio_1 = L / H_corrige if H_corrige > 0 else 0

        # Ratio 2: (largeur - bandeau_droit) / (hauteur - bandeau_sup)
        L_corrige = L - 32  # Bandeau droit
        ratio_2 = L_corrige / H_corrige if H_corrige > 0 else 0

        print(f"{w['titre']:<20} {L}x{H:<10} {ratio_brut:<12.4f} {ratio_1:<12.4f} {ratio_2:<12.4f}")

    print("-" * 80)

    # Analyse détaillée
    print("\n" + "=" * 80)
    print("ANALYSE DÉTAILLÉE")
    print("=" * 80)

    for w in bluestacks_windows:
        L = w['largeur']
        H = w['hauteur']
        H_corrige = H - BANDEAU_SUPERIEUR
        L_corrige = L - 32

        print(f"\n>>> {w['titre']} <<<")
        print(f"  Position: ({w['x']}, {w['y']})")
        print(f"  Dimensions brutes: {L} x {H}")
        print(f"  Dimensions corrigées (H-32): {L} x {H_corrige}")
        print(f"  Dimensions corrigées (L-32, H-32): {L_corrige} x {H_corrige}")
        print()
        print(f"  Ratio brut L/H:           {L/H:.4f}")
        print(f"  Ratio 1 L/(H-32):         {L/H_corrige:.4f}")
        print(f"  Ratio 2 (L-32)/(H-32):    {L_corrige/H_corrige:.4f}")

        # Comparaison avec ratio cible
        ratio_cible = 600 / 1040  # 0.5769
        print()
        print(f"  Ratio cible (600/1040):   {ratio_cible:.4f}")
        print(f"  Diff ratio brut:          {abs(L/H - ratio_cible):.4f}")
        print(f"  Diff ratio 1:             {abs(L/H_corrige - ratio_cible):.4f}")
        print(f"  Diff ratio 2:             {abs(L_corrige/H_corrige - ratio_cible):.4f}")

        # Détection pub basée sur les différents ratios
        SEUIL = 0.70
        print()
        print(f"  Détection pub (seuil {SEUIL}):")
        print(f"    - Via ratio brut:    {'OUI' if L/H > SEUIL else 'NON'}")
        print(f"    - Via ratio 1:       {'OUI' if L/H_corrige > SEUIL else 'NON'}")
        print(f"    - Via ratio 2:       {'OUI' if L_corrige/H_corrige > SEUIL else 'NON'}")

    print("\n" + "=" * 80)
    print("RECOMMANDATION")
    print("=" * 80)
    print("""
Si le ratio 2 (L-32)/(H-32) est proche de 0.577 pour les fenêtres SANS pub,
alors le bandeau supérieur fait bien ~32px.

Sinon, essayez d'autres valeurs pour BANDEAU_SUPERIEUR (ligne 8 du script):
  - 40px, 50px, 60px, 70px, etc.

Le bon BANDEAU_SUPERIEUR est celui qui donne un ratio 2 ≈ 0.577 sans pub.
""")

    input("\nAppuyez sur Entrée pour quitter...")


if __name__ == "__main__":
    main()
