# -*- coding: utf-8 -*-
"""Manoir virtuel pour tests

ManoirVirtuel est un manoir de test qui n'a pas de fenêtre Windows réelle.
Il log périodiquement qu'il est en train de travailler.
"""
import time

from manoirs.manoir_base import ManoirBase
from manoirs.config_manoirs import get_config
import actions.liste_actions as ListeActions




class ManoirVirtuel(ManoirBase):
    """Manoir virtuel pour tests

    N'a pas de fenêtre Windows réelle.
    Log périodiquement qu'il est actif.
    """

    def __init__(self, manoir_id="virtuel", config=None):
        """
        Args:
            manoir_id: Identifiant unique
            config: Configuration (dict) ou None pour charger depuis config_manoirs
        """
        if config is None:
            config = get_config(manoir_id) or {}

        super().__init__(
            manoir_id=manoir_id,
            nom=config.get("nom", "Manoir Virtuel"),
            titre_bluestacks=None,  # Pas de fenêtre Windows
            priorite=config.get("priorite", 30),
            slots_config=config.get("slots_config", [{'nom': 'default', 'nb': 1}]),
        )

        self.intervalle_log = config.get("intervalle_log", 30)
        self._action_log = None
    
    # =========================================================
    # SURCHARGE - Pas de fenêtre Windows réelle
    # =========================================================
    
    def find_window(self):
        """Pas de fenêtre Windows - toujours None"""
        return None
    
    def activate(self):
        """Pas de fenêtre à activer - toujours True"""
        self.logger.debug(f"Manoir virtuel {self.nom} activé (simulé)")
        return True
    
    def is_valid(self):
        """Manoir virtuel toujours valide"""
        return True
    
    def get_rect(self):
        """Pas de rectangle - retourne une zone fictive"""
        return (0, 0, self.largeur, self.hauteur)
    
    def capture(self, force=False):
        """Pas de capture réelle - retourne None sans erreur"""
        return None
    
    # =========================================================
    # SURCHARGE - Ignorer détection d'images/texte
    # =========================================================
    
    def detect_image(self, template_path, threshold=None, region=None):
        """Pas de détection d'image - toujours False"""
        return False
    
    def find_image(self, template_path, threshold=None, region=None):
        """Pas de recherche d'image - toujours None"""
        return None
    
    def click_image(self, template_path, threshold=None, offset=(0, 0)):
        """Pas de clic sur image - toujours False"""
        return False
    
    def detect_text(self, text, region=None):
        """Pas de détection de texte - toujours False"""
        return False
    
    def find_text(self, text, region=None):
        """Pas de recherche de texte - toujours None"""
        return None
    
    def click_at(self, x, y):
        """Pas de clic réel - simulé"""
        self.logger.debug(f"Clic simulé à ({x}, {y})")
        return True
    
    # =========================================================
    # IMPLÉMENTATION ABSTRAITE
    # =========================================================

    def _preparer_alimenter_sequence(self):
        """Alimente la séquence - toujours prêt

        Returns:
            bool: Toujours True (manoir virtuel toujours prêt)
        """
        return True

    def definir_timers(self):
        """Pas de timers pour le manoir virtuel"""
        pass
    
    def initialiser_sequence(self):
        """Initialise l'action de log périodique"""
        self._action_log = ListeActions.ActionLogPeriodique(
            self,
            message="Je suis en train de travailler------------------------------------------------",
            duree_secondes=self.intervalle_log
        )
        # Ajouter l'action à la séquence une seule fois
        self.sequence.add(self._action_log)


def creer_manoir_virtuel(manoir_id="virtuel"):
    """Factory function pour créer un manoir virtuel

    Args:
        manoir_id: ID du manoir

    Returns:
        ManoirVirtuel
    """
    return ManoirVirtuel(manoir_id)
