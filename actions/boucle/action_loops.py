# -*- coding: utf-8 -*-
"""Actions de boucle For et While avec gestion de l'arrêt et sauvegarde d'état"""
import uuid
from actions.item import Item


class ActionFor(Item):
    """Boucle avec compteur (nombre fixe ou dynamique d'itérations)
    
    La boucle peut être interrompue via doit_casser = True.
    L'itération en cours (atomique) se termine avant l'arrêt.
    L'état (compteur) est sauvegardé pour reprise ultérieure.
    
    Exemple:
        ActionFor(
            fenetre,
            nombre_iterations=10,  # ou lambda f: f.nb_mercenaires_restants
            actions=[ActionTuerMercenaire(fenetre)],
            nom_boucle="tuer_mercenaires"  # Pour sauvegarde état
        )
    """
    
    def __init__(self, fenetre, nombre_iterations, actions, nom_boucle=None):
        """
        Args:
            fenetre: Instance de FenetreBase
            nombre_iterations: Nombre fixe ou fonction lambda(fenetre) -> int
            actions: Liste d'actions à exécuter à chaque itération
            nom_boucle: Nom unique pour sauvegarde/reprise (optionnel)
        """
        super().__init__(fenetre)
        self.nombre_iterations = nombre_iterations
        self.actions = actions if isinstance(actions, list) else [actions]
        self.nom_boucle = nom_boucle
        
        self.compteur = 0
        self.loop_id = str(uuid.uuid4())
        self.doit_casser = False
        self._iteration_en_cours = False
        
        # S'enregistrer dans les boucles actives de la fenêtre
        self.fenetre.boucles_actives[self.loop_id] = self
    
    def _get_nombre_total(self):
        """Retourne le nombre total d'itérations (PROTÉGÉ)"""
        if callable(self.nombre_iterations):
            return self.nombre_iterations(self.fenetre)
        return self.nombre_iterations
    
    def _run(self):
        """Gère une itération de la boucle (PROTÉGÉ)
        
        Returns:
            bool: True si itération lancée, False si boucle terminée
        """
        # Vérifier si on doit s'arrêter
        if self.doit_casser:
            self.logger.info(
                f"ActionFor '{self.nom_boucle or self.loop_id}': "
                f"arrêt demandé après {self.compteur} itérations"
            )
            self._sauvegarder_etat()
            self._nettoyer()
            return False
        
        # Obtenir le nombre total d'itérations
        n = self._get_nombre_total()
        
        # Vérifier si on a terminé
        if self.compteur >= n:
            self.logger.debug(
                f"ActionFor '{self.nom_boucle or self.loop_id}': "
                f"terminée ({self.compteur}/{n})"
            )
            self._nettoyer()
            return True
        
        # Incrémenter le compteur
        self.compteur += 1
        self._iteration_en_cours = True
        
        self.logger.debug(
            f"ActionFor '{self.nom_boucle or self.loop_id}': "
            f"itération {self.compteur}/{n}"
        )
        
        # Ajouter les actions de cette itération + la boucle elle-même
        # La boucle se réinsère après les actions pour continuer
        actions_iteration = self.actions.copy()
        actions_iteration.append(self)  # Réinsertion pour prochaine itération
        
        self.fenetre.sequence.add_next(actions_iteration)
        
        return True
    
    def _sauvegarder_etat(self):
        """Sauvegarde l'état de la boucle pour reprise (PROTÉGÉ)"""
        if self.nom_boucle:
            # Sauvegarder dans la fenêtre pour persistance
            if not hasattr(self.fenetre, '_etats_boucles'):
                self.fenetre._etats_boucles = {}
            
            self.fenetre._etats_boucles[self.nom_boucle] = {
                'compteur': self.compteur,
                'nombre_total': self._get_nombre_total(),
            }
            
            self.logger.info(
                f"ActionFor '{self.nom_boucle}': état sauvegardé "
                f"(compteur={self.compteur})"
            )
    
    def _nettoyer(self):
        """Se retire des boucles actives (PROTÉGÉ)"""
        if self.loop_id in self.fenetre.boucles_actives:
            del self.fenetre.boucles_actives[self.loop_id]
    
    def reprendre(self, compteur_depart):
        """Reprend la boucle à partir d'un compteur donné
        
        Args:
            compteur_depart: Valeur du compteur pour reprendre
        """
        self.compteur = compteur_depart
        self.doit_casser = False
        self.logger.info(
            f"ActionFor '{self.nom_boucle or self.loop_id}': "
            f"reprise au compteur {compteur_depart}"
        )
    
    def __repr__(self):
        n = self._get_nombre_total() if not callable(self.nombre_iterations) else "?"
        return (
            f"ActionFor('{self.nom_boucle or 'anonymous'}', "
            f"compteur={self.compteur}/{n})"
        )


class ActionWhile(Item):
    """Boucle conditionnelle avec sécurité (max iterations)
    
    Continue tant que la condition est vraie.
    La condition est réévaluée à chaque itération (pas de cache).
    
    Exemple:
        ActionWhile(
            fenetre,
            condition_func=lambda f: f.slots_disponibles > 0,
            actions=[ActionEnvoyerTroupes(fenetre)],
            max_iterations=100,
            nom_boucle="envoyer_troupes"
        )
    """
    
    MAX_ITERATIONS_DEFAULT = 1000  # Sécurité anti boucle infinie
    
    def __init__(self, fenetre, condition_func, actions, 
                 max_iterations=None, nom_boucle=None):
        """
        Args:
            fenetre: Instance de FenetreBase
            condition_func: Fonction lambda(fenetre) -> bool
            actions: Liste d'actions à exécuter à chaque itération
            max_iterations: Limite de sécurité (défaut: 1000)
            nom_boucle: Nom unique pour sauvegarde/reprise (optionnel)
        """
        super().__init__(fenetre, condition_func)
        self.actions = actions if isinstance(actions, list) else [actions]
        self.max_iterations = max_iterations or self.MAX_ITERATIONS_DEFAULT
        self.nom_boucle = nom_boucle
        
        self.compteur = 0
        self.loop_id = str(uuid.uuid4())
        self.doit_casser = False
        
        # S'enregistrer dans les boucles actives
        self.fenetre.boucles_actives[self.loop_id] = self
    
    def condition(self):
        """Override : réévalue TOUJOURS la condition (pas de cache)
        
        Returns:
            bool: Résultat de la condition
        """
        if self.condition_func is not None:
            self.resultat_condition = self.condition_func(self.fenetre)
        else:
            self.resultat_condition = True
        return self.resultat_condition
    
    def _run(self):
        """Gère une itération de la boucle (PROTÉGÉ)
        
        Returns:
            bool: True si itération lancée, False si boucle terminée
        """
        # Vérifier si on doit s'arrêter
        if self.doit_casser:
            self.logger.info(
                f"ActionWhile '{self.nom_boucle or self.loop_id}': "
                f"arrêt demandé après {self.compteur} itérations"
            )
            self._sauvegarder_etat()
            self._nettoyer()
            return False
        
        # Vérifier la limite de sécurité
        if self.compteur >= self.max_iterations:
            self.logger.error(
                f"ActionWhile '{self.nom_boucle or self.loop_id}': "
                f"limite de sécurité atteinte ({self.max_iterations})"
            )
            self._nettoyer()
            return False
        
        # Incrémenter le compteur
        self.compteur += 1
        
        self.logger.debug(
            f"ActionWhile '{self.nom_boucle or self.loop_id}': "
            f"itération {self.compteur}"
        )
        
        # Ajouter les actions + la boucle pour continuer
        actions_iteration = self.actions.copy()
        actions_iteration.append(self)
        
        self.fenetre.sequence.add_next(actions_iteration)
        
        return True
    
    def _sauvegarder_etat(self):
        """Sauvegarde l'état de la boucle (PROTÉGÉ)"""
        if self.nom_boucle:
            if not hasattr(self.fenetre, '_etats_boucles'):
                self.fenetre._etats_boucles = {}
            
            self.fenetre._etats_boucles[self.nom_boucle] = {
                'compteur': self.compteur,
            }
            
            self.logger.info(
                f"ActionWhile '{self.nom_boucle}': état sauvegardé "
                f"(compteur={self.compteur})"
            )
    
    def _nettoyer(self):
        """Se retire des boucles actives (PROTÉGÉ)"""
        if self.loop_id in self.fenetre.boucles_actives:
            del self.fenetre.boucles_actives[self.loop_id]
    
    def reprendre(self, compteur_depart=0):
        """Reprend la boucle
        
        Args:
            compteur_depart: Valeur du compteur pour reprendre
        """
        self.compteur = compteur_depart
        self.doit_casser = False
        self.logger.info(
            f"ActionWhile '{self.nom_boucle or self.loop_id}': "
            f"reprise au compteur {compteur_depart}"
        )
    
    def __repr__(self):
        return (
            f"ActionWhile('{self.nom_boucle or 'anonymous'}', "
            f"compteur={self.compteur}, max={self.max_iterations})"
        )
