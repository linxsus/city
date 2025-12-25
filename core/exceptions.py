"""
Exceptions personnalisées pour le système de gestion d'états et chemins.
"""


class ErreurConfiguration(Exception):
    """
    Exception levée lorsque le fichier TOML de configuration est invalide ou manquant.
    Provoque l'arrêt du programme.
    """
    pass


class ErreurValidation(Exception):
    """
    Exception levée lors de la validation du système (références invalides, noms dupliqués).
    Provoque l'arrêt au démarrage.
    """
    pass


class EtatInconnuException(Exception):
    """
    Exception levée lorsqu'un nom d'état inexistant est demandé.
    """
    pass


class AucunEtatTrouve(Exception):
    """
    Exception levée lorsque determiner_etat_actuel() ne trouve aucun état correspondant
    et qu'il n'y a pas d'EtatInconnuGlobal configuré.
    """
    pass
