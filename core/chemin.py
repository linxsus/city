"""
Classe Chemin - Représente une transition possible entre deux états.

Un chemin contient les actions nécessaires pour effectuer la transition.
"""

from typing import List, Union, Callable, Any, Optional, TYPE_CHECKING
from abc import abstractmethod

if TYPE_CHECKING:
    from core.etat import Etat
    from core.etat_inconnu import EtatInconnu


class Chemin:
    """
    Représente une transition possible entre deux états.

    Attributes:
        etat_initial: État de départ (instance, string ou classe)
        etat_sortie: État(s) d'arrivée:
            - None: sortie inconnue complète
            - Etat: sortie certaine
            - List[Etat]: liste d'états possibles
            - EtatInconnu: utilise etats_possibles de l'EtatInconnu
        fonction_actions: Fonction générant les actions de transition

    Notes:
        Pas de Singleton - il peut y avoir plusieurs chemins pour la même transition.
    """

    etat_initial: Union['Etat', str, type] = None
    etat_sortie: Union['Etat', 'EtatInconnu', List['Etat'], str, type, None] = None

    def __init__(self):
        """Initialise le chemin."""
        pass

    @abstractmethod
    def fonction_actions(self) -> List[Any]:
        """
        Génère la liste d'actions pour effectuer la transition.

        Returns:
            Liste d'objets Action du framework

        Raises:
            Peut lever des exceptions selon l'implémentation
        """
        pass

    def generer_actions(self) -> List[Any]:
        """
        Appelle fonction_actions pour obtenir la liste d'actions.

        Returns:
            Liste d'objets Action du framework

        Raises:
            Peut lever les exceptions de fonction_actions
        """
        return self.fonction_actions()

    def est_certain(self) -> bool:
        """
        Détermine si ce chemin a une sortie certaine.

        Returns:
            True si la sortie est certaine (une seule instance d'Etat),
            False sinon (null, liste ou EtatInconnu)
        """
        from core.etat import Etat
        from core.etat_inconnu import EtatInconnu

        if self.etat_sortie is None:
            return False

        if isinstance(self.etat_sortie, list):
            return False

        if isinstance(self.etat_sortie, EtatInconnu):
            return False

        if isinstance(self.etat_sortie, Etat):
            return True

        return False

    def __repr__(self) -> str:
        initial = getattr(self.etat_initial, 'nom', str(self.etat_initial))
        sortie = getattr(self.etat_sortie, 'nom', str(self.etat_sortie))
        return f"{self.__class__.__name__}({initial} → {sortie})"

    def __str__(self) -> str:
        initial = getattr(self.etat_initial, 'nom', str(self.etat_initial))
        sortie = getattr(self.etat_sortie, 'nom', str(self.etat_sortie))
        return f"{initial} → {sortie}"
