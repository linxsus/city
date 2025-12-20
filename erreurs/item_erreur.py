# -*- coding: utf-8 -*-
"""ItemErreur - Gestion des erreurs détectables visuellement

Un ItemErreur représente une erreur qui peut être détectée à l'écran
(popup, message, etc.) et corrigée automatiquement.
"""
from pathlib import Path

import actions.liste_actions as ListeActions
from utils.config import TEMPLATES_POPUPS_DIR
from utils.logger import get_module_logger

logger = get_module_logger("ItemErreur")


class ItemErreur(ListeActions.Item):
    """Représente une erreur détectable et corrigeable
    
    Une erreur est détectée par :
    - Une image (popup, bouton)
    - Un texte (message OCR)
    - Une couleur à une position
    
    Une fois détectée, l'erreur peut :
    - Exécuter une action de correction
    - Demander un retry de l'action originale
    - Exclure la fenêtre de la rotation
    
    Attributes:
        image: Chemin vers l'image template de l'erreur
        texte: Texte à chercher (OCR)
        couleur: Tuple (x, y, rgb, tolerance) pour détection couleur
        message: Message descriptif de l'erreur
        action_correction: Action à exécuter pour corriger
        retry_action_originale: Si True, retry l'action qui a causé l'erreur
        exclure_fenetre: Durée d'exclusion en secondes (0 = pas d'exclusion)
        priorite: Priorité de l'erreur (plus haut = vérifié en premier)
    """
    
    def __init__(self, fenetre, 
                 image=None, 
                 texte=None, 
                 couleur=None,
                 message=None,
                 action_correction=None,
                 retry_action_originale=False,
                 exclure_fenetre=0,
                 priorite=0,
                 region=None,
                 threshold=None):
        """
        Args:
            fenetre: Instance de FenetreBase
            image: Chemin vers l'image template (relatif à templates/popups/)
            texte: Texte à chercher (OCR)
            couleur: Tuple (x, y, (r,g,b), tolerance) pour détection
            message: Message descriptif
            action_correction: Action ou liste d'actions à exécuter
            retry_action_originale: Retry l'action originale après correction
            exclure_fenetre: Durée d'exclusion en secondes
            priorite: Priorité de vérification
            region: Région de recherche (x, y, w, h) optionnelle
            threshold: Seuil de confiance pour image (0-1)
        """
        super().__init__(fenetre)
        
        # Méthode de détection
        self.image = image
        self.texte = texte
        self.couleur = couleur
        self.region = region
        self.threshold = threshold
        
        # Informations
        self.message = message or self._generate_message()
        self.priorite = priorite
        
        # Actions
        self.action_correction = action_correction
        self.retry_action_originale = retry_action_originale
        self.exclure_fenetre = exclure_fenetre
        
        # Référence à l'action qui a déclenché l'erreur
        self.action_originale = None
    
    def _generate_message(self):
        """Génère un message par défaut (PROTÉGÉ)"""
        if self.image:
            return f"Erreur détectée: {Path(self.image).stem}"
        elif self.texte:
            return f"Erreur détectée: '{self.texte}'"
        elif self.couleur:
            return f"Erreur détectée: couleur à ({self.couleur[0]}, {self.couleur[1]})"
        return "Erreur détectée"
    
    def _get_image_path(self):
        """Retourne le chemin complet de l'image (PROTÉGÉ)"""
        if not self.image:
            return None
        
        # Si c'est déjà un chemin absolu
        if Path(self.image).is_absolute():
            return self.image
        
        # Sinon, relatif à templates/popups/
        return str(TEMPLATES_POPUPS_DIR / self.image)
    
    def condition(self):
        """Détecte si l'erreur est présente
        
        Returns:
            bool: True si l'erreur est détectée
        """
        # Ne pas utiliser le cache pour les erreurs
        # (on veut toujours réévaluer)
        
        detected = False
        
        try:
            if self.image:
                detected = self._detect_image()
            elif self.texte:
                detected = self._detect_text()
            elif self.couleur:
                detected = self._detect_color()
        except Exception as e:
            logger.error(f"Erreur lors de la détection: {e}")
            detected = False
        
        if detected:
            logger.debug(f"Erreur détectée: {self.message}")
        
        return detected
    
    def _detect_image(self):
        """Détecte l'erreur par image (PROTÉGÉ)"""
        image_path = self._get_image_path()
        if not image_path:
            return False
        
        # Utiliser le détecteur de la fenêtre
        return self.fenetre.detect_image(
            image_path, 
            threshold=self.threshold,
            region=self.region
        )
    
    def _detect_text(self):
        """Détecte l'erreur par texte OCR (PROTÉGÉ)"""
        return self.fenetre.detect_text(self.texte, region=self.region)
    
    def _detect_color(self):
        """Détecte l'erreur par couleur (PROTÉGÉ)"""
        x, y, rgb, tolerance = self.couleur
        return self.fenetre.check_color_at(x, y, rgb, tolerance)
    
    def _run(self):
        """Exécute la correction de l'erreur (PROTÉGÉ)
        
        Returns:
            bool: True si correction réussie
        """
        logger.info(f"Correction de l'erreur: {self.message}")
        
        # Exécuter l'action de correction si présente
        if self.action_correction:
            try:
                if isinstance(self.action_correction, list):
                    # Liste d'actions à ajouter à la séquence
                    self.fenetre.sequence.add_next(self.action_correction)
                else:
                    # Action unique à exécuter directement
                    self.action_correction.execute()
            except Exception as e:
                logger.error(f"Erreur lors de la correction: {e}")
                return False
        
        # Exclure la fenêtre si demandé
        if self.exclure_fenetre > 0:
            self._exclure_fenetre()
        
        return True
    
    def _exclure_fenetre(self):
        """Exclut la fenêtre de la rotation (PROTÉGÉ)"""
        from core.window_state_manager import get_window_state_manager
        
        wsm = get_window_state_manager()
        
        if self.exclure_fenetre >= 7200:  # 2h ou plus
            wsm.set_exclu_2h(self.fenetre.fenetre_id, self.message)
        else:
            wsm.set_exclu_temporaire(self.fenetre.fenetre_id, self.exclure_fenetre)
        
        logger.info(
            f"Fenêtre {self.fenetre.fenetre_id} exclue pour "
            f"{self.exclure_fenetre}s: {self.message}"
        )
    
    def __repr__(self):
        detection = self.image or self.texte or "couleur"
        return f"ItemErreur('{detection}', priorite={self.priorite})"


class ItemErreurImage(ItemErreur):
    """ItemErreur spécialisé pour la détection par image
    
    Simplifie la création d'erreurs basées sur des popups/boutons.
    """
    
    def __init__(self, fenetre, image, message=None, **kwargs):
        """
        Args:
            fenetre: Instance de FenetreBase
            image: Nom du fichier image (dans templates/popups/)
            message: Message descriptif
            **kwargs: Arguments passés à ItemErreur
        """
        super().__init__(fenetre, image=image, message=message, **kwargs)


class ItemErreurTexte(ItemErreur):
    """ItemErreur spécialisé pour la détection par texte OCR"""
    
    def __init__(self, fenetre, texte, message=None, **kwargs):
        """
        Args:
            fenetre: Instance de FenetreBase
            texte: Texte à chercher
            message: Message descriptif
            **kwargs: Arguments passés à ItemErreur
        """
        super().__init__(fenetre, texte=texte, message=message, **kwargs)


class ItemErreurCouleur(ItemErreur):
    """ItemErreur spécialisé pour la détection par couleur"""
    
    def __init__(self, fenetre, x, y, rgb, tolerance=10, message=None, **kwargs):
        """
        Args:
            fenetre: Instance de FenetreBase
            x, y: Position du pixel à vérifier
            rgb: Couleur attendue (r, g, b)
            tolerance: Tolérance par composante
            message: Message descriptif
            **kwargs: Arguments passés à ItemErreur
        """
        couleur = (x, y, rgb, tolerance)
        super().__init__(fenetre, couleur=couleur, message=message, **kwargs)
