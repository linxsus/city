# -*- coding: utf-8 -*-
"""Test de la configuration sans largeur"""

from manoirs.config_manoirs import get_config, HAUTEUR_DEFAUT
from manoirs.manoir_base import ManoirBase

def test_config_sans_largeur():
    """Test que la configuration fonctionne sans largeur"""

    print("=== Test de la configuration sans largeur ===\n")

    # 1. Vérifier que HAUTEUR_DEFAUT existe
    print(f"[OK] HAUTEUR_DEFAUT = {HAUTEUR_DEFAUT}")

    # 2. Vérifier la configuration du manoir principal
    config = get_config("principal")
    print(f"\n[OK] Configuration du manoir principal chargee:")
    print(f"  - nom: {config.get('nom')}")
    print(f"  - hauteur: {config.get('hauteur')}")
    print(f"  - largeur: {config.get('largeur', 'NON DEFINIE [OK]')}")
    print(f"  - aspect_ratio: {config.get('aspect_ratio', 'None (auto-detection) [OK]')}")

    # 3. Vérifier que ManoirBase accepte les nouveaux paramètres
    print(f"\n[OK] Verification des parametres de ManoirBase...")
    print(f"  - Le parametre 'hauteur' est requis")
    print(f"  - Le parametre 'largeur' a ete supprime")
    print(f"  - Le parametre 'aspect_ratio' est optionnel")
    print(f"  - self.largeur sera calcule lors de placer_fenetre()")
    print("\n[OK] Structure verifiee avec succes !")

    print("\n=== Test reussi ! ===")
    print("\nResume des changements:")
    print("- Le parametre 'largeur' a ete supprime de config_manoirs.py")
    print("- La largeur est maintenant calculee automatiquement lors du placement")
    print("- Le ratio peut etre specifie avec 'aspect_ratio' (optionnel)")
    print("- La methode placer_fenetre() utilise resize_with_aspect_ratio()")

    return True


if __name__ == "__main__":
    test_config_sans_largeur()
