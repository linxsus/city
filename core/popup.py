"""
Classe Popup - État popup avec génération automatique de chemin.

Un popup est un état qui peut être fermé par un clic, générant automatiquement
le chemin de fermeture correspondant.
"""

from typing import TYPE_CHECKING, Any, List, Optional

from core.chemin import Chemin
from core.etat import Etat
from core.etat_inconnu import EtatInconnu

if TYPE_CHECKING:
    from manoirs.manoir_base import ManoirBase


class Popup(Etat):
    """
    État popup avec génération automatique de chemin de fermeture.

    Hérite de Etat et génère automatiquement un CheminPopup correspondant.
    Le GestionnaireEtats détecte les Popup et enregistre leurs chemins.

    Attributes:
        image_detection: Chemin vers l'image pour détecter le popup
        image_fermeture: Image à cliquer pour fermer (si None, utilise image_detection)
        position_fermeture: Position (x, y) alternative au clic image
        etats_possibles_extra: États supplémentaires possibles après fermeture
                               (en plus de ceux définis par le groupe dans le TOML)

    Notes:
        - Si image_fermeture est None, on clique sur image_detection
        - Si position_fermeture est défini, il a priorité sur l'image
        - Les états de sortie sont calculés automatiquement par le GestionnaireEtats
          à partir des groupes définis dans le TOML + etats_possibles_extra
    """

    image_detection: str = None
    image_fermeture: Optional[str] = None
    position_fermeture: Optional[tuple] = None
    position_relative: bool = False
    etats_possibles_extra: List[str] = []

    def __init__(self):
        """Initialise le popup."""
        super().__init__()
        # Par défaut, les popups sont dans le groupe "popup"
        if "popup" not in self.groupes:
            self.groupes = self.groupes + ["popup"]

    def verif(self, manoir: "ManoirBase") -> bool:
        """
        Vérifie si le popup est actuellement affiché.

        Args:
            manoir: Instance du manoir pour accéder aux méthodes de détection

        Returns:
            True si le popup est visible, False sinon
        """
        if self.image_detection is None:
            return False
        return manoir.detect_image(self.image_detection)

    def generer_chemin(self) -> "CheminPopup":
        """
        Génère le chemin de fermeture pour ce popup.

        Returns:
            Instance de CheminPopup configurée pour fermer ce popup
        """
        return CheminPopup(self)


class CheminPopup(Chemin):
    """
    Chemin généré automatiquement pour fermer un popup.

    Créé par Popup.generer_chemin(), ce chemin contient les actions
    nécessaires pour fermer le popup.

    Attributes:
        popup: Instance du Popup associé
    """

    def __init__(self, popup: Popup):
        """
        Initialise le chemin à partir du popup.

        Args:
            popup: Instance du Popup à fermer

        Note:
            etat_sortie est initialisé vide et sera défini par
            GestionnaireEtats._resoudre_groupes_sortie() après le scan
        """
        super().__init__()
        self.popup = popup
        self.etat_initial = popup.nom
        # etat_sortie sera défini par GestionnaireEtats._resoudre_groupes_sortie()
        self.etat_sortie = EtatInconnu(etats_possibles=[])

    def fonction_actions(self, manoir: Any) -> List[Any]:
        """
        Génère les actions pour fermer le popup.

        Args:
            manoir: Instance du manoir

        Returns:
            Liste d'actions pour fermer le popup
        """
        from actions.simple.action_simple import ActionSimple

        from actions.action_reprise_preparer_tour import ActionReprisePreparerTour
        from actions.simple.action_bouton import ActionBouton

        actions = []

        if self.popup.position_fermeture:
            # Clic positionnel
            x, y = self.popup.position_fermeture
            relative = self.popup.position_relative

            def clic_fermer(m, px=x, py=y, rel=relative):
                m.click_at(px, py, relative=rel)
                return True

            actions.append(
                ActionSimple(
                    manoir, action_func=clic_fermer, nom=f"Fermer{self.popup.__class__.__name__}"
                )
            )
        else:
            # Clic sur image
            image = self.popup.image_fermeture or self.popup.image_detection
            actions.append(ActionBouton(manoir, image))

        # Toujours ajouter ActionReprisePreparerTour pour re-détecter l'état
        actions.append(ActionReprisePreparerTour(manoir))

        return actions

    def __repr__(self) -> str:
        return f"CheminPopup({self.popup.nom} → fermeture)"
