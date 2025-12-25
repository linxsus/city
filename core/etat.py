"""
Classe de base Etat avec pattern Singleton.

Un état représente un écran ou une situation identifiable du système (ex: ville, carte, popup).
"""

from typing import List, Optional
from abc import abstractmethod


class SingletonMeta(type):
    """
    Métaclasse garantissant le pattern Singleton pour les classes Etat.
    Chaque classe dérivée ne peut avoir qu'une seule instance.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

    @classmethod
    def clear_instances(mcs):
        """Efface toutes les instances (utile pour les tests)."""
        mcs._instances.clear()


class Etat(metaclass=SingletonMeta):
    """
    Représente un état/écran du système.

    Pattern: Singleton (une seule instance par classe)

    Attributes:
        nom: Identifiant unique de l'état
        groupes: Liste des groupes d'appartenance (ex: "popup", "ecran_principal")
    """

    nom: str = None
    groupes: List[str] = []

    def __init__(self):
        if self.nom is None:
            self.nom = self.__class__.__name__

    @abstractmethod
    def verif(self) -> bool:
        """
        Vérifie si le système est actuellement dans cet état.

        Returns:
            True si l'état actuel correspond, False sinon.

        Notes:
            Implémentation spécifique dans chaque classe dérivée.
            Doit utiliser des méthodes de détection (OCR, image matching, etc.)
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(nom='{self.nom}')"

    def __str__(self) -> str:
        return self.nom
