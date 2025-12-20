# -*- coding: utf-8 -*-
"""
Résolution du système d'équations pour trouver les bandeaux BlueStacks

Hypothèse: Les bandeaux (pub, droit, supérieur) sont de taille FIXE en pixels.
On cherche pub, bd, bs tels que le ratio (L - pub - bd) / (H - bs) soit constant.
"""

def resoudre_bandeaux(mesures,
                       pub_range=(0, 400),
                       bd_range=(0, 60),
                       bs_range=(0, 100)):
    """
    Trouve les valeurs de pub, bandeau_droit, bandeau_sup qui minimisent
    la variance du ratio de la zone de jeu.

    Args:
        mesures: Liste de tuples (largeur, hauteur)
        pub_range: (min, max) pour la pub
        bd_range: (min, max) pour le bandeau droit
        bs_range: (min, max) pour le bandeau supérieur

    Returns:
        Liste des meilleures solutions
    """
    solutions = []

    for pub in range(pub_range[0], pub_range[1]):
        for bd in range(bd_range[0], bd_range[1]):
            for bs in range(bs_range[0], bs_range[1]):
                ratios = []
                valid = True

                for L, H in mesures:
                    zone_L = L - pub - bd
                    zone_H = H - bs

                    if zone_L <= 0 or zone_H <= 0:
                        valid = False
                        break

                    ratios.append(zone_L / zone_H)

                if valid and len(ratios) == len(mesures):
                    mean = sum(ratios) / len(ratios)
                    variance = sum((r - mean)**2 for r in ratios) / len(ratios)
                    max_diff = max(ratios) - min(ratios)

                    solutions.append({
                        'pub': pub,
                        'bd': bd,
                        'bs': bs,
                        'ratio': mean,
                        'variance': variance,
                        'max_diff': max_diff,
                        'ratios': ratios
                    })

    # Trier par variance
    solutions.sort(key=lambda x: x['variance'])

    return solutions


def afficher_resultats(solutions, mesures, top_n=20):
    """Affiche les résultats de manière lisible"""

    print("=" * 80)
    print(f"TOP {top_n} SOLUTIONS (variance minimale)")
    print("=" * 80)
    print(f"{'Pub':<6} {'BD':<5} {'BS':<5} {'Ratio':<10} {'Variance':<14} {'Max diff':<10}")
    print("-" * 80)

    for s in solutions[:top_n]:
        print(f"{s['pub']:<6} {s['bd']:<5} {s['bs']:<5} {s['ratio']:<10.4f} {s['variance']:<14.10f} {s['max_diff']:<10.6f}")

    if solutions:
        best = solutions[0]
        print("\n" + "=" * 80)
        print("MEILLEURE SOLUTION")
        print("=" * 80)
        print(f"\n  Pub (gauche)       = {best['pub']} px")
        print(f"  Bandeau droit      = {best['bd']} px")
        print(f"  Bandeau supérieur  = {best['bs']} px")
        print(f"  Ratio zone de jeu  = {best['ratio']:.6f}")
        print(f"  Variance           = {best['variance']:.10f}")
        print(f"  Différence max     = {best['max_diff']:.6f}")

        print("\n  Vérification détaillée:")
        print(f"  {'#':<4} {'L':<6} {'H':<6} {'Zone L':<8} {'Zone H':<8} {'Ratio':<10}")
        print("  " + "-" * 50)

        for i, (L, H) in enumerate(mesures, 1):
            zone_L = L - best['pub'] - best['bd']
            zone_H = H - best['bs']
            ratio = zone_L / zone_H
            print(f"  {i:<4} {L:<6} {H:<6} {zone_L:<8} {zone_H:<8} {ratio:<10.6f}")


def main():
    print("\n" + "=" * 80)
    print("RÉSOLUTION DES BANDEAUX BLUESTACKS")
    print("Structure: [PUB] [ZONE DE JEU] [BANDEAU DROIT]")
    print("           [BANDEAU SUPÉRIEUR au-dessus de tout]")
    print("=" * 80)

    # Mesures fournies (fenêtres avec pub)
    mesures = [
        (806, 878),
        (883, 992),
        (790, 854),
        (495, 525),
    ]

    print("\nMesures entrées:")
    for i, (L, H) in enumerate(mesures, 1):
        print(f"  Fenêtre {i}: {L} x {H} (ratio brut: {L/H:.4f})")

    # Résolution avec toutes les fenêtres
    print("\n" + "=" * 80)
    print("ANALYSE AVEC TOUTES LES FENÊTRES (4)")
    print("=" * 80)

    solutions_all = resoudre_bandeaux(mesures)
    afficher_resultats(solutions_all, mesures)

    # Résolution sans la fenêtre 4 (trop petite)
    print("\n\n" + "=" * 80)
    print("ANALYSE SANS LA FENÊTRE 4 (trop petite)")
    print("=" * 80)

    mesures_3 = mesures[:3]
    solutions_3 = resoudre_bandeaux(mesures_3)
    afficher_resultats(solutions_3, mesures_3)

    # Test de la solution sur la fenêtre 4
    if solutions_3:
        best = solutions_3[0]
        L4, H4 = mesures[3]
        zone_L4 = L4 - best['pub'] - best['bd']
        zone_H4 = H4 - best['bs']

        print(f"\n  Test sur fenêtre 4 ({L4}x{H4}):")
        if zone_L4 > 0 and zone_H4 > 0:
            ratio4 = zone_L4 / zone_H4
            print(f"  Zone: {zone_L4} x {zone_H4}, Ratio: {ratio4:.6f}")
            print(f"  Écart avec ratio moyen: {abs(ratio4 - best['ratio']):.6f}")
        else:
            print(f"  ⚠️  Dimensions négatives! ({zone_L4} x {zone_H4})")

    print("\n" + "=" * 80)
    print("FORMULES POUR LE CODE")
    print("=" * 80)

    if solutions_3:
        best = solutions_3[0]
        print(f"""
# Constantes à utiliser dans config_manoirs.py:
BLUESTACKS_PUB = {best['pub']}              # Largeur de la pub (gauche)
BLUESTACKS_BANDEAU_DROIT = {best['bd']}     # Bandeau droit avec icônes
BLUESTACKS_BANDEAU_SUP = {best['bs']}       # Bandeau supérieur (titre + navigation)
BLUESTACKS_TOTAL_LARGEUR = {best['pub'] + best['bd']}  # Total à soustraire en largeur

# Ratio de la zone de jeu (après soustraction des bandeaux):
BLUESTACKS_RATIO_ZONE_JEU = {best['ratio']:.6f}

# Pour calculer la zone de jeu à partir des dimensions de la fenêtre:
# zone_largeur = largeur_fenetre - BLUESTACKS_PUB - BLUESTACKS_BANDEAU_DROIT
# zone_hauteur = hauteur_fenetre - BLUESTACKS_BANDEAU_SUP
""")

    input("\nAppuyez sur Entrée pour quitter...")


if __name__ == "__main__":
    main()
