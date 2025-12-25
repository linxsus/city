"""
Classe EtatInconnu - État spécial représentant un état incertain.

Utilisé comme état de sortie de chemins dont le résultat est imprévisible.
"""

from typing import List, Union, TYPE_CHECKING
from core.etat import Etat

if TYPE_CHECKING:
    from core.etat import Etat


class EtatInconnu(Etat):
    """
    État spécial représentant un état incertain.

    Utilisé comme état de sortie de chemins dont le résultat est imprévisible.
    La liste etats_possibles contient les états à tester pour déterminer l'état réel.

    Attributes:
        etats_possibles: Liste des états à tester pour déterminer l'état réel.
                        Si vide, tous les états enregistrés seront testés.
    """

    etats_possibles: List[Union['Etat', str, type]] = []

    def verif(self) -> bool:
        """
        Un état inconnu ne peut jamais être l'état actuel réel.

        Returns:
            Toujours False
        """
        return False

    def __repr__(self) -> str:
        possibles = [str(e) for e in self.etats_possibles]
        return f"{self.__class__.__name__}(nom='{self.nom}', etats_possibles={possibles})"
