"""Action atomique avec gestion d'erreurs à 2 niveaux"""

import time

from actions.item import Item
from utils.config import CAPTURES_DIR


class Action(Item):
    """Action atomique avec gestion d'erreurs

    Deux niveaux de gestion d'erreurs :
    1. erreurs_verif_apres : Erreurs à vérifier APRÈS exécution réussie
    2. erreurs_si_echec : Erreurs à vérifier SI l'action échoue

    Attributes:
        erreurs_verif_apres: Liste d'ItemErreur à vérifier après succès
        erreurs_si_echec: Liste d'ItemErreur à vérifier après échec
        retry_si_erreur_non_identifiee: Retry automatique si erreur inconnue
        delai_verification: Délai avant vérification des erreurs (secondes)
    """

    def __init__(
        self,
        fenetre,
        condition_func=None,
        erreurs_verif_apres=None,
        erreurs_si_echec=None,
        retry_si_erreur_non_identifiee=False,
        delai_verification=1.0,
        log_erreur_si_echec=True,
    ):
        """
        Args:
            fenetre: Instance de FenetreBase
            condition_func: Fonction de condition optionnelle
            erreurs_verif_apres: Liste d'erreurs à vérifier après succès
            erreurs_si_echec: Liste d'erreurs à vérifier après échec
            retry_si_erreur_non_identifiee: Si True, retry 1 fois si erreur inconnue
            delai_verification: Délai avant vérification des erreurs
            log_erreur_si_echec: Si False, ne pas logger quand _run() retourne False
        """
        super().__init__(fenetre, condition_func)
        self.erreurs_verif_apres = erreurs_verif_apres or []
        self.erreurs_si_echec = erreurs_si_echec or []
        self.retry_si_erreur_non_identifiee = retry_si_erreur_non_identifiee
        self.delai_verification = delai_verification
        self.log_erreur_si_echec = log_erreur_si_echec
        self._deja_retry_non_identifie = False  # Flag pour retry unique

    def execute(self):
        """Exécute l'action avec gestion d'erreurs complète

        Returns:
            bool: True si succès final, False sinon
        """
        # Vérifier la condition
        if not self.condition():
            self.executer = True
            return False

        # Exécuter l'action
        result = self._run()
        erreur_identifiee = False

        # ========== VÉRIFICATION POST-ACTION ==========
        if result and self.erreurs_verif_apres and self.delai_verification > 0:
            time.sleep(self.delai_verification)

            for err in self.erreurs_verif_apres:
                err.action_originale = self
                if err.condition():  # Erreur détectée
                    erreur_identifiee = True
                    self.logger.warning(f"Erreur post-action : {err.message or err.image}")
                    result = False
                    err.execute()  # Exécute la correction

                    # L'erreur décide si retry
                    if err.retry_action_originale:
                        self.logger.info("Retry de l'action après correction")
                        self.reset_condition()
                        self._deja_retry_non_identifie = False
                        result = self._run()

                    break  # Une seule erreur traitée à la fois

        # ========== GESTION D'ÉCHEC ==========
        if not result:
            if self.log_erreur_si_echec:
                self._log_erreur()

            # Vérifier les erreurs "si échec"
            for err in self.erreurs_si_echec:
                err.action_originale = self
                if err.condition():
                    erreur_identifiee = True
                    self.logger.warning(f"Erreur si_echec : {err.message or err.image}")
                    err.execute()

                    if err.retry_action_originale:
                        self.logger.info("Retry de l'action après correction (si_echec)")
                        self.reset_condition()
                        self._deja_retry_non_identifie = False
                        result = self._run()

                    break

            # ========== RETRY SI ERREUR NON IDENTIFIÉE ==========
            if not erreur_identifiee and self.retry_si_erreur_non_identifiee:
                if not self._deja_retry_non_identifie:
                    self._deja_retry_non_identifie = True
                    self.logger.warning("Erreur non identifiée - Retry automatique (1 fois)")
                    self.reset_condition()
                    time.sleep(1)  # Petite pause avant retry
                    result = self._run()
                else:
                    self.logger.error("Échec après retry - Abandon")

        self.executer = True
        return result

    def _log_erreur(self):
        """Log l'erreur et prend un screenshot (PROTÉGÉ)"""
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        nom_fichier = CAPTURES_DIR / f"erreur_{self.__class__.__name__}_{timestamp}.png"

        self.logger.error("Erreur d'exécution")

        try:
            # Créer le dossier si nécessaire
            CAPTURES_DIR.mkdir(parents=True, exist_ok=True)

            # Capturer l'écran
            screenshot = self.fenetre.capture(force=True)
            if screenshot:
                screenshot.save(str(nom_fichier))
                self.logger.debug(f"Screenshot sauvegardé : {nom_fichier}")
        except Exception as e:
            self.logger.error(f"Erreur capture screenshot: {e}")

    def _run(self):
        """Méthode à implémenter par les sous-classes (PROTÉGÉ)

        Returns:
            bool: True si succès, False sinon
        """
        raise NotImplementedError(f"{self.__class__.__name__} doit implémenter _run()")


class ActionSimple(Action):
    """Action simple définie par une fonction

    Utile pour créer des actions rapides sans définir une classe.
    """

    def __init__(self, fenetre, action_func, nom=None, **kwargs):
        """
        Args:
            fenetre: Instance de FenetreBase
            action_func: Fonction lambda(fenetre) -> bool
            nom: Nom optionnel pour le logging
            **kwargs: Arguments passés à Action
        """
        super().__init__(fenetre, **kwargs)
        self.action_func = action_func
        self.nom = nom or "ActionSimple"

    def _run(self):
        """Exécute la fonction d'action"""
        try:
            return self.action_func(self.fenetre)
        except Exception as e:
            self.logger.error(f"{self.nom}: {e}")
            return False

    def __repr__(self):
        return f"ActionSimple({self.nom})"
