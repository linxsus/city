"""État : Popup Connexion quotidienne"""

from core.popup import Popup


class EtatPopupConnexion(Popup):
    """État quand le popup Connexion quotidienne est affiché

    Détection :
    - Template popups/connexion_quotidienne.png visible

    Fermeture :
    - Clic sur le popup pour collecter

    Priorité haute : les popups doivent être détectés avant les états normaux.
    Note: États de sortie définis par groupe "ville" dans config/etat-chemin.toml
    """

    nom = "popup_connexion"
    groupes = ["popup", "demarrage"]
    image_detection = "popups/connexion_quotidienne.png"
    etats_possibles_extra = ["chargement"]
