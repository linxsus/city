# -*- coding: utf-8 -*-
"""
Created on Sun Dec  7 12:39:42 2025

@author: xavie
"""
import time
from actions.action import Action



class ActionAttendre(Action):
    """Attend un délai sans bloquer le moteur
    
    Permet au moteur de continuer à traiter les autres fenêtres
    pendant l'attente. L'action se remet dans la séquence et
    demande une rotation vers la fenêtre suivante.
    
    Fonctionnement:
    1. Première exécution : démarre le timer interne
    2. Si délai non écoulé : rewind(1) + demande_rotation → passe à fenêtre suivante
    3. Prochains tours : vérifie le timer
    4. Timer écoulé : return True et continue la séquence
    
    Exemple:
        ActionAttendre(fenetre, 120)  # Attend 2 minutes
    """
    
    def __init__(self, fenetre, duree_secondes):
        """
        Args:
            fenetre: Instance de FenetreBase
            duree_secondes: Durée d'attente en secondes
        """
        super().__init__(fenetre, log_erreur_si_echec=False)
        self.nom = "AttendreNonBloquante"
        self.duree = duree_secondes
        self._debut = None
    
    def _run(self):
        """Vérifie le timer et demande rotation si pas prêt"""
        # Première exécution : démarrer le timer
        if self._debut is None:
            self._debut = time.time()
            self.fenetre.logger.info(
                f"Attente non bloquante démarrée: {self.duree}s"
            )
        
        # Vérifier si le délai est écoulé
        temps_ecoule = time.time() - self._debut
        temps_restant = self.duree - temps_ecoule
        
        if temps_ecoule < self.duree:
            # Pas encore prêt
            self.fenetre.logger.debug(
                f"Attente en cours: {temps_restant:.1f}s restantes"
            )
            
            # 1. Se remettre dans la séquence pour être réexécuté
            self.fenetre.sequence.rewind(1)
            
            # 2. Demander à Engine de passer à la fenêtre suivante
            self.fenetre.demander_rotation()
            
            return True  # L'action s'est bien exécutée (on attend juste)
        
        # Timer écoulé, on peut continuer
        self.fenetre.logger.info(
            f"Attente non bloquante terminée après {temps_ecoule:.1f}s"
        )
        self.reset()  # Reset pour prochaine utilisation
        return True
    
    def reset(self):
        """Reset le timer pour réutilisation"""
        self._debut = None
    
    def __repr__(self):
        if self._debut:
            temps_ecoule = time.time() - self._debut
            return f"ActionAttendreNonBloquante({self.duree}s, écoulé={temps_ecoule:.1f}s)"
        return f"ActionAttendreNonBloquante({self.duree}s)"

