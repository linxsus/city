# -*- coding: utf-8 -*-
"""Classe de base pour tous les éléments exécutables"""


class Item:
    """Classe de base pour tous les éléments exécutables (actions, boucles, etc.)

    Attributes:
        fenetre: Référence à la fenêtre propriétaire
        condition_func: Fonction de condition optionnelle
        resultat_condition: Cache du résultat de la condition
        executer: Flag indiquant si l'item a été exécuté
    """

    def __init__(self, fenetre, condition_func=None):
        """
        Args:
            fenetre: Instance de FenetreBase
            condition_func: Fonction lambda(fenetre) -> bool, optionnelle
        """
        self.fenetre = fenetre
        self.condition_func = condition_func
        self.resultat_condition = None
        self.executer = False

    def condition(self):
        """Évalue la condition avec cache

        Returns:
            bool: Résultat de la condition (True par défaut)
        """
        if self.resultat_condition is not None:
            return self.resultat_condition

        if self.condition_func is not None:
            self.resultat_condition = self.condition_func(self.fenetre)
        else:
            self.resultat_condition = True

        return self.resultat_condition

    def reset_condition(self):
        """Réinitialise le cache de la condition"""
        self.resultat_condition = None

    def execute(self):
        """Template Method : vérifie condition puis appelle _run()

        Returns:
            bool: Résultat de l'exécution
        """
        if self.condition():
            result = self._run()
        else:
            result = False

        self.executer = True
        return result

    def _run(self):
        """Méthode à implémenter par les sous-classes (PROTÉGÉ)

        Returns:
            bool: True si succès, False sinon

        Raises:
            NotImplementedError: Si non implémenté dans la sous-classe
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} doit implémenter _run()"
        )


# =====================================================
# HELPERS DE CONDITIONS
# =====================================================

def image_presente(image_path, threshold=0.8):
    """Condition : une image est présente à l'écran

    Args:
        image_path: Chemin vers l'image template
        threshold: Seuil de confiance (0-1)

    Returns:
        Fonction lambda pour la condition
    """
    return lambda f: f.detect_image(image_path, threshold)


def image_absente(image_path, threshold=0.8):
    """Condition : une image n'est PAS présente à l'écran

    Args:
        image_path: Chemin vers l'image template
        threshold: Seuil de confiance (0-1)

    Returns:
        Fonction lambda pour la condition
    """
    return lambda f: not f.detect_image(image_path, threshold)


def texte_present(texte, region=None):
    """Condition : un texte est présent à l'écran (OCR)

    Args:
        texte: Texte à chercher
        region: Région optionnelle (x, y, width, height)

    Returns:
        Fonction lambda pour la condition
    """
    return lambda f: f.detect_text(texte, region)


def texte_absent(texte, region=None):
    """Condition : un texte n'est PAS présent à l'écran

    Args:
        texte: Texte à chercher
        region: Région optionnelle (x, y, width, height)

    Returns:
        Fonction lambda pour la condition
    """
    return lambda f: not f.detect_text(texte, region)


def variable_egale(var_name, valeur):
    """Condition : une variable de la fenêtre égale une valeur

    Args:
        var_name: Nom de l'attribut de la fenêtre
        valeur: Valeur attendue

    Returns:
        Fonction lambda pour la condition
    """
    return lambda f: getattr(f, var_name, None) == valeur


def variable_superieure(var_name, valeur):
    """Condition : une variable de la fenêtre est supérieure à une valeur

    Args:
        var_name: Nom de l'attribut de la fenêtre
        valeur: Valeur de comparaison

    Returns:
        Fonction lambda pour la condition
    """
    return lambda f: getattr(f, var_name, 0) > valeur


def variable_inferieure(var_name, valeur):
    """Condition : une variable de la fenêtre est inférieure à une valeur

    Args:
        var_name: Nom de l'attribut de la fenêtre
        valeur: Valeur de comparaison

    Returns:
        Fonction lambda pour la condition
    """
    return lambda f: getattr(f, var_name, 0) < valeur


def variable_superieure_ou_egale(var_name, valeur):
    """Condition : une variable >= valeur

    Args:
        var_name: Nom de l'attribut de la fenêtre
        valeur: Valeur de comparaison

    Returns:
        Fonction lambda pour la condition
    """
    return lambda f: getattr(f, var_name, 0) >= valeur


def variable_inferieure_ou_egale(var_name, valeur):
    """Condition : une variable <= valeur

    Args:
        var_name: Nom de l'attribut de la fenêtre
        valeur: Valeur de comparaison

    Returns:
        Fonction lambda pour la condition
    """
    return lambda f: getattr(f, var_name, 0) <= valeur


def et(*conditions):
    """Combine plusieurs conditions avec ET logique

    Args:
        *conditions: Fonctions de condition

    Returns:
        Fonction lambda pour la condition combinée
    """
    return lambda f: all(c(f) for c in conditions)


def ou(*conditions):
    """Combine plusieurs conditions avec OU logique

    Args:
        *conditions: Fonctions de condition

    Returns:
        Fonction lambda pour la condition combinée
    """
    return lambda f: any(c(f) for c in conditions)


def non(condition):
    """Inverse une condition (NOT logique)

    Args:
        condition: Fonction de condition

    Returns:
        Fonction lambda pour la condition inversée
    """
    return lambda f: not condition(f)


def toujours_vrai():
    """Condition toujours vraie

    Returns:
        Fonction lambda retournant True
    """
    return lambda f: True


def toujours_faux():
    """Condition toujours fausse

    Returns:
        Fonction lambda retournant False
    """
    return lambda f: False
