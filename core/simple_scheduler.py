"""Ordonnanceur à deux niveaux pour la sélection des fenêtres

Gère deux niveaux de priorité :
1. PRIORITAIRE : Actions urgentes (collectes, popups, erreurs...)
2. NORMAL : Actions standard (mercenaires, construction...)

Logique :
- Tant qu'une fenêtre a des actions prioritaires prêtes, on reste en niveau prioritaire
- Quand plus aucune action prioritaire n'est prête, on passe au niveau normal
"""

from dataclasses import dataclass
from typing import Any, Optional

from utils.logger import get_module_logger

logger = get_module_logger("SimpleScheduler")


@dataclass
class ManoirSelection:
    """Résultat de sélection d'un manoir

    Attributes:
        manoir_id: ID du manoir sélectionné
        temps_avant_passage: Temps en secondes avant que le manoir soit prêt
        priorite: Priorité statique du manoir
        est_prioritaire: True si action prioritaire, False si normale
        pret: True si le manoir est prêt maintenant (temps <= 0)
    """

    manoir_id: str
    temps_avant_passage: float
    priorite: int
    est_prioritaire: bool
    pret: bool

    def __repr__(self):
        niveau_str = "PRIO" if self.est_prioritaire else "NORM"
        if self.pret:
            return (
                f"ManoirSelection({self.manoir_id}, [{niveau_str}] PRÊT, priorité={self.priorite})"
            )
        return f"ManoirSelection({self.manoir_id}, [{niveau_str}] dans {self.temps_avant_passage:.1f}s, priorité={self.priorite})"


class SimpleScheduler:
    """Ordonnanceur à deux niveaux

    Interroge chaque manoir sur ses deux listes de slots (prioritaire et normale)
    et sélectionne selon la logique :
    1. S'il existe un manoir avec action prioritaire prête → sélectionner
    2. Sinon → sélectionner parmi les normales

    Le manoir doit implémenter :
        - get_prochain_passage_prioritaire() -> float : secondes avant prochain traitement prioritaire
        - get_prochain_passage_normal() -> float : secondes avant prochain traitement normal
        - priorite : int : priorité statique (plus haut = plus prioritaire)

    Retour des méthodes get_prochain_passage_*() :
        - <= 0 : prêt maintenant
        - > 0  : revenir dans X secondes
        - float('inf') ou None : pas d'action de ce type
    """

    def __init__(self):
        """Initialise l'ordonnanceur"""
        pass

    def _collecter_selections(
        self, manoirs: dict[str, Any], prioritaire: bool
    ) -> list[ManoirSelection]:
        """Collecte les sélections pour un niveau donné (PROTÉGÉ)

        Args:
            manoirs: Dictionnaire {manoir_id: manoir}
            prioritaire: True pour collecter les prioritaires, False pour les normales

        Returns:
            Liste de ManoirSelection pour ce niveau
        """
        selections = []
        niveau_str = "prioritaire" if prioritaire else "normal"

        for manoir_id, manoir in manoirs.items():
            try:
                if prioritaire:
                    temps = manoir.get_prochain_passage_prioritaire()
                else:
                    temps = manoir.get_prochain_passage_normal()

                # Ignorer si pas d'action (None ou inf)
                if temps is None or temps == float("inf"):
                    continue

                priorite_statique = getattr(manoir, "priorite", 0)

                selection = ManoirSelection(
                    manoir_id=manoir_id,
                    temps_avant_passage=temps,
                    priorite=priorite_statique,
                    est_prioritaire=prioritaire,
                    pret=(temps <= 0),
                )
                selections.append(selection)

            except AttributeError:
                # Méthode non implémentée, ignorer ce niveau pour ce manoir
                pass
            except Exception as e:
                logger.error(f"Erreur collecte {niveau_str} pour {manoir_id}: {e}")

        return selections

    def selectionner_manoir(self, manoirs: dict[str, Any]) -> Optional[ManoirSelection]:
        """Sélectionne le manoir à traiter

        Logique :
        1. Collecter tous les manoirs avec actions prioritaires
        2. Si au moins un est prêt (temps <= 0) → sélectionner parmi les prioritaires
        3. Sinon → sélectionner parmi les normales

        Args:
            manoirs: Dictionnaire {manoir_id: manoir}

        Returns:
            ManoirSelection ou None si aucun manoir
        """
        if not manoirs:
            logger.debug("Aucun manoir à sélectionner")
            return None

        # 1. Collecter les prioritaires
        prioritaires = self._collecter_selections(manoirs, prioritaire=True)

        # 2. Vérifier si un prioritaire est prêt
        prioritaires_prets = [s for s in prioritaires if s.pret]

        if prioritaires_prets:
            # Trier par priorité décroissante (temps = 0 pour tous)
            prioritaires_prets.sort(key=lambda s: -s.priorite)
            meilleur = prioritaires_prets[0]
            logger.info(f"[PRIORITAIRE] Manoir sélectionné: {meilleur}")
            return meilleur

        # 3. Aucun prioritaire prêt → passer au niveau normal
        normales = self._collecter_selections(manoirs, prioritaire=False)

        # Combiner prioritaires non prêts + normales pour choisir le plus proche
        tous = prioritaires + normales

        if not tous:
            logger.debug("Aucune action disponible")
            return None

        # Trier par temps croissant, puis priorité décroissante
        tous.sort(key=lambda s: (s.temps_avant_passage, -s.priorite))

        meilleur = tous[0]
        niveau_str = "PRIORITAIRE" if meilleur.est_prioritaire else "NORMAL"
        logger.info(f"[{niveau_str}] Manoir sélectionné: {meilleur}")

        return meilleur

    def get_classement(self, manoirs: dict[str, Any]) -> dict[str, list[ManoirSelection]]:
        """Retourne le classement complet par niveau

        Args:
            manoirs: Dictionnaire {manoir_id: manoir}

        Returns:
            Dict avec clés 'prioritaire' et 'normal', chacune contenant une liste triée
        """
        prioritaires = self._collecter_selections(manoirs, prioritaire=True)
        normales = self._collecter_selections(manoirs, prioritaire=False)

        # Trier chaque niveau
        prioritaires.sort(key=lambda s: (s.temps_avant_passage, -s.priorite))
        normales.sort(key=lambda s: (s.temps_avant_passage, -s.priorite))

        return {"prioritaire": prioritaires, "normal": normales}

    def get_temps_attente(self, manoirs: dict[str, Any]) -> Optional[float]:
        """Retourne le temps d'attente avant le prochain manoir prêt

        Args:
            manoirs: Dictionnaire {manoir_id: manoir}

        Returns:
            Secondes à attendre, 0 si un manoir est prêt, None si aucun manoir
        """
        selection = self.selectionner_manoir(manoirs)

        if selection is None:
            return None

        if selection.pret:
            return 0

        return selection.temps_avant_passage

    def a_prioritaire_pret(self, manoirs: dict[str, Any]) -> bool:
        """Vérifie si une action prioritaire est prête

        Args:
            manoirs: Dictionnaire {manoir_id: manoir}

        Returns:
            True si au moins un manoir a une action prioritaire prête
        """
        prioritaires = self._collecter_selections(manoirs, prioritaire=True)
        return any(s.pret for s in prioritaires)

    def __repr__(self):
        return "SimpleScheduler(2 niveaux: PRIORITAIRE, NORMAL)"


# Instance globale
_simple_scheduler_instance = None


def get_simple_scheduler() -> SimpleScheduler:
    """Retourne l'instance singleton du SimpleScheduler

    Returns:
        SimpleScheduler: Instance partagée
    """
    global _simple_scheduler_instance
    if _simple_scheduler_instance is None:
        _simple_scheduler_instance = SimpleScheduler()
    return _simple_scheduler_instance
