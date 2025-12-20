# -*- coding: utf-8 -*-
"""Test de la logique de placement avec gestion de la largeur"""

def simuler_placement(largeur_config, hauteur_config, ratio_fenetre, position_x_config):
    """Simule la logique de placement

    Args:
        largeur_config: Largeur de reference dans la config
        hauteur_config: Hauteur cible
        ratio_fenetre: Ratio actuel de la fenetre (l/h)
        position_x_config: Position X configuree
    """
    print(f"\n{'='*60}")
    print(f"Configuration:")
    print(f"  - Largeur config: {largeur_config}px (zone de reference)")
    print(f"  - Hauteur config: {hauteur_config}px")
    print(f"  - Position X config: {position_x_config}px")
    print(f"  - Ratio fenetre actuel: {ratio_fenetre:.3f}")

    # Calculer la largeur selon le ratio et la hauteur
    largeur_calculee = int(hauteur_config * ratio_fenetre)

    print(f"\nCalcul:")
    print(f"  - Largeur calculee = {hauteur_config} * {ratio_fenetre:.3f} = {largeur_calculee}px")

    # Verifier la coherence
    if largeur_calculee < largeur_config:
        print(f"\nResultat: ERREUR!")
        print(f"  - Largeur calculee ({largeur_calculee}px) < largeur config ({largeur_config}px)")
        print(f"  - La zone de jeu sera trop petite pour le positionnement!")
        print(f"  - Position finale: x={position_x_config}, y=0")

    elif largeur_calculee > largeur_config:
        decalage = largeur_calculee - largeur_config
        nouvelle_x = position_x_config - decalage

        print(f"\nResultat: AJUSTEMENT")
        print(f"  - Largeur calculee ({largeur_calculee}px) > largeur config ({largeur_config}px)")
        print(f"  - Decalage: {decalage}px")
        print(f"  - Position ajustee: x = {position_x_config} - {decalage} = {nouvelle_x}px")
        print(f"  - Position finale: x={nouvelle_x}, y=0")

    else:
        print(f"\nResultat: PARFAIT!")
        print(f"  - Largeur calculee ({largeur_calculee}px) = largeur config ({largeur_config}px)")
        print(f"  - Position finale: x={position_x_config}, y=0")


def main():
    print("="*60)
    print("TEST DE LA LOGIQUE DE PLACEMENT")
    print("="*60)

    # Cas 1: Fenetre parfaitement dimensionnee (ratio = largeur_config / hauteur_config)
    print("\n--- CAS 1: Ratio parfait ---")
    simuler_placement(
        largeur_config=600,
        hauteur_config=1040,
        ratio_fenetre=600/1040,  # 0.577
        position_x_config=0
    )

    # Cas 2: Fenetre trop large (largeur calculee > config)
    print("\n--- CAS 2: Fenetre plus large (ratio plus grand) ---")
    simuler_placement(
        largeur_config=600,
        hauteur_config=1040,
        ratio_fenetre=0.7,  # Plus large que 600/1040 = 0.577
        position_x_config=0
    )

    # Cas 3: Fenetre trop etroite (largeur calculee < config) - ERREUR
    print("\n--- CAS 3: Fenetre trop etroite (ratio trop petit) ---")
    simuler_placement(
        largeur_config=600,
        hauteur_config=1040,
        ratio_fenetre=0.5,  # Plus etroit que 600/1040 = 0.577
        position_x_config=0
    )

    # Cas 4: Avec position X non nulle
    print("\n--- CAS 4: Position X = 100, fenetre plus large ---")
    simuler_placement(
        largeur_config=600,
        hauteur_config=1040,
        ratio_fenetre=0.7,
        position_x_config=100
    )

    print(f"\n{'='*60}")
    print("CONCLUSION:")
    print("- La largeur config sert de zone de reference")
    print("- La largeur reelle est calculee selon le ratio de la fenetre")
    print("- Si trop large: on decale vers la gauche (x peut etre negatif)")
    print("- Si trop etroit: ERREUR loggee (zone insuffisante)")
    print("="*60)


if __name__ == "__main__":
    main()
