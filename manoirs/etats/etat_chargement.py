# -*- coding: utf-8 -*-
"""État : BlueStacks en cours de chargement"""

from core.etat import Etat


class EtatChargement(Etat):
    """État quand BlueStacks est ouvert et en cours de chargement

    Détection :
    - Fenêtre BlueStacks présente
    - Lancement initié par nous (flag _lancement_initie)
    - Icône jeu_charge NON visible

    Note:
        Le flag _lancement_initie est mis à True par chemin_lancer_bluestacks
        et remis à False par etat_ville ou manoir.reset()
    """
    nom = "chargement"
    groupes = ["demarrage"]

    def verif(self, manoir) -> bool:
        """Vérifie si BlueStacks charge (lancé par nous, jeu pas prêt)

        Args:
            manoir: Instance du manoir

        Returns:
            True si en cours de chargement (et lancé par nous)
        """
        # Fenêtre doit exister
        hwnd = manoir.find_window()
        if hwnd is None:
            return False

        # Doit avoir été lancé par nous
        if not getattr(manoir, '_lancement_initie', False):
            return False

        # Icône jeu chargé ne doit PAS être visible
        if manoir.detect_image("ville/icone_jeu_charge.png"):
            return False

        return True
