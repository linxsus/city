# -*- coding: utf-8 -*-
"""Test de la detection de deplacement/redimensionnement"""

def tester_besoin_placement(position_attendue, position_actuelle, fenetre_placee, tolerance=5):
    """Teste si un placement est necessaire

    Args:
        position_attendue: Tuple (x, y, w, h) attendu ou None
        position_actuelle: Tuple (x, y, w, h) actuel
        fenetre_placee: Bool, True si deja placee une fois
        tolerance: Tolerance en pixels

    Returns:
        bool: True si placement necessaire
    """
    x_act, y_act, w_act, h_act = position_actuelle

    # Si jamais placee, placement necessaire
    if not fenetre_placee:
        return True, "Premier placement"

    # Si deja placee mais pas de position attendue, placement necessaire
    if not position_attendue:
        return True, "Position attendue inconnue"

    x_att, y_att, w_att, h_att = position_attendue

    # Comparer avec tolerance
    if (abs(x_act - x_att) <= tolerance and
        abs(y_act - y_att) <= tolerance and
        abs(w_act - w_att) <= tolerance and
        abs(h_act - h_att) <= tolerance):
        return False, "Position inchangee"
    else:
        return True, f"Position changee: ({x_act}, {y_act}, {w_act}x{h_act}) != ({x_att}, {y_att}, {w_att}x{h_att})"


def main():
    print("="*70)
    print("TEST DE DETECTION DE DEPLACEMENT/REDIMENSIONNEMENT")
    print("="*70)

    # Cas 1: Premier placement
    print("\n--- CAS 1: Premier placement (demarrage) ---")
    besoin, raison = tester_besoin_placement(
        position_attendue=None,
        position_actuelle=(100, 100, 600, 1040),
        fenetre_placee=False
    )
    print(f"Position actuelle: (100, 100, 600x1040)")
    print(f"Position attendue: None")
    print(f"Fenetre placee: False")
    print(f"Resultat: {'PLACER' if besoin else 'NE PAS PLACER'} - {raison}")

    # Cas 2: Fenetre deja placee, position inchangee
    print("\n--- CAS 2: Fenetre deja placee, position inchangee ---")
    besoin, raison = tester_besoin_placement(
        position_attendue=(-128, 0, 728, 1040),
        position_actuelle=(-128, 0, 728, 1040),
        fenetre_placee=True
    )
    print(f"Position actuelle: (-128, 0, 728x1040)")
    print(f"Position attendue: (-128, 0, 728x1040)")
    print(f"Fenetre placee: True")
    print(f"Resultat: {'PLACER' if besoin else 'NE PAS PLACER'} - {raison}")

    # Cas 3: Fenetre deplacee par l'utilisateur
    print("\n--- CAS 3: Fenetre deplacee par l'utilisateur ---")
    besoin, raison = tester_besoin_placement(
        position_attendue=(-128, 0, 728, 1040),
        position_actuelle=(50, 100, 728, 1040),  # Deplacee a (50, 100)
        fenetre_placee=True
    )
    print(f"Position actuelle: (50, 100, 728x1040)")
    print(f"Position attendue: (-128, 0, 728x1040)")
    print(f"Fenetre placee: True")
    print(f"Resultat: {'PLACER' if besoin else 'NE PAS PLACER'} - {raison}")

    # Cas 4: Fenetre redimensionnee par l'utilisateur
    print("\n--- CAS 4: Fenetre redimensionnee par l'utilisateur ---")
    besoin, raison = tester_besoin_placement(
        position_attendue=(-128, 0, 728, 1040),
        position_actuelle=(-128, 0, 800, 1200),  # Redimensionnee
        fenetre_placee=True
    )
    print(f"Position actuelle: (-128, 0, 800x1200)")
    print(f"Position attendue: (-128, 0, 728x1040)")
    print(f"Fenetre placee: True")
    print(f"Resultat: {'PLACER' if besoin else 'NE PAS PLACER'} - {raison}")

    # Cas 5: Variation minime (bordures Windows)
    print("\n--- CAS 5: Variation minime dans la tolerance (bordures Windows) ---")
    besoin, raison = tester_besoin_placement(
        position_attendue=(-128, 0, 728, 1040),
        position_actuelle=(-126, 2, 730, 1042),  # +/-2-3px
        fenetre_placee=True,
        tolerance=5
    )
    print(f"Position actuelle: (-126, 2, 730x1042)")
    print(f"Position attendue: (-128, 0, 728x1040)")
    print(f"Fenetre placee: True")
    print(f"Tolerance: 5px")
    print(f"Resultat: {'PLACER' if besoin else 'NE PAS PLACER'} - {raison}")

    print("\n" + "="*70)
    print("CONCLUSION:")
    print("- Premier placement: TOUJOURS placer")
    print("- Fenetre inchangee (tolerance 5px): NE PAS placer")
    print("- Fenetre deplacee/redimensionnee: REPLACER automatiquement")
    print("="*70)


if __name__ == "__main__":
    main()
