"""Service de gestion des erreurs détectables."""

import ast
import re
from pathlib import Path

from ..config import PROJECT_ROOT
from ..models.schemas import ErreurSchema, TypeErreur


class ErreurService:
    """Service pour charger et gérer les erreurs du framework."""

    def __init__(self):
        self.erreurs_file = PROJECT_ROOT / "erreurs" / "liste_erreurs.py"
        self._erreurs_cache: list[ErreurSchema] | None = None
        self._categories = [
            "connexion",
            "jeu",
            "popup",
            "systeme",
            "autre",
        ]

    def get_all_erreurs(self) -> list[ErreurSchema]:
        """Récupère toutes les erreurs définies dans liste_erreurs.py.

        Returns:
            Liste des erreurs parsées
        """
        if self._erreurs_cache is not None:
            return self._erreurs_cache

        self._erreurs_cache = self._parse_erreurs_file()
        return self._erreurs_cache

    def get_erreurs_by_category(self, categorie: str) -> list[ErreurSchema]:
        """Récupère les erreurs d'une catégorie spécifique.

        Args:
            categorie: Catégorie à filtrer

        Returns:
            Liste des erreurs de la catégorie
        """
        return [e for e in self.get_all_erreurs() if e.categorie == categorie]

    def get_categories(self) -> list[str]:
        """Retourne la liste des catégories disponibles."""
        return self._categories

    def get_erreur_by_nom(self, nom: str) -> ErreurSchema | None:
        """Récupère une erreur par son nom.

        Args:
            nom: Nom de l'erreur

        Returns:
            L'erreur ou None si non trouvée
        """
        for erreur in self.get_all_erreurs():
            if erreur.nom == nom:
                return erreur
        return None

    def get_erreurs_verif_apres_defaults(self) -> list[str]:
        """Retourne les noms des erreurs à vérifier par défaut après chaque action.

        Returns:
            Liste des noms d'erreurs
        """
        return [
            "compte_utilise",
            "connexion_perdue",
            "popup_evenement",
            "popup_recompense",
        ]

    def get_erreurs_si_echec_defaults(self) -> list[str]:
        """Retourne les noms des erreurs à vérifier par défaut si échec.

        Returns:
            Liste des noms d'erreurs
        """
        return [
            "ressources_insuffisantes",
            "slots_pleins",
            "file_attente_pleine",
            "cible_introuvable",
            "troupes_insuffisantes",
            "erreur_reseau",
            "app_ne_repond_pas",
        ]

    def invalidate_cache(self):
        """Invalide le cache des erreurs."""
        self._erreurs_cache = None

    def _parse_erreurs_file(self) -> list[ErreurSchema]:
        """Parse le fichier liste_erreurs.py pour extraire les erreurs.

        Returns:
            Liste des erreurs parsées
        """
        if not self.erreurs_file.exists():
            return []

        try:
            content = self.erreurs_file.read_text(encoding="utf-8")
            return self._extract_erreurs_from_content(content)
        except Exception as e:
            print(f"Erreur lors du parsing de liste_erreurs.py: {e}")
            return []

    def _extract_erreurs_from_content(self, content: str) -> list[ErreurSchema]:
        """Extrait les erreurs du contenu du fichier.

        Args:
            content: Contenu du fichier Python

        Returns:
            Liste des erreurs
        """
        erreurs = []
        current_category = "autre"

        # Pattern pour les commentaires de section
        section_pattern = re.compile(r"#\s*=+\s*\n#\s*(.+?)\s*\n#\s*=+")

        # Trouver toutes les sections
        sections = []
        for match in section_pattern.finditer(content):
            section_name = match.group(1).lower()
            if "connexion" in section_name:
                sections.append((match.start(), "connexion"))
            elif "jeu" in section_name:
                sections.append((match.start(), "jeu"))
            elif "popup" in section_name or "information" in section_name or "publicité" in section_name:
                sections.append((match.start(), "popup"))
            elif "système" in section_name or "systeme" in section_name or "bluestacks" in section_name:
                sections.append((match.start(), "systeme"))
            else:
                sections.append((match.start(), "autre"))

        # Pattern pour les définitions d'erreurs
        # erreurs["nom"] = ItemErreurImage(...) ou ItemErreurTexte(...)
        erreur_pattern = re.compile(
            r'erreurs\["(\w+)"\]\s*=\s*(ItemErreurImage|ItemErreurTexte)\(\s*'
            r'fenetre,\s*'
            r'(?:image|texte)="([^"]+)",\s*'
            r'message="([^"]+)"',
            re.MULTILINE | re.DOTALL
        )

        for match in erreur_pattern.finditer(content):
            pos = match.start()
            nom = match.group(1)
            type_class = match.group(2)
            detection_value = match.group(3)
            message = match.group(4)

            # Déterminer la catégorie basée sur la position
            category = "autre"
            for section_pos, section_cat in reversed(sections):
                if pos > section_pos:
                    category = section_cat
                    break

            # Déterminer le type
            if type_class == "ItemErreurImage":
                erreur_type = TypeErreur.IMAGE
                image = detection_value
                texte = None
            else:
                erreur_type = TypeErreur.TEXTE
                image = None
                texte = detection_value

            # Extraire les autres paramètres
            block_end = content.find(")", pos)
            block = content[pos:block_end]

            retry = "retry_action_originale=True" in block
            exclure = self._extract_exclure_fenetre(block)
            priorite = self._extract_priorite(block)

            erreur = ErreurSchema(
                nom=nom,
                type=erreur_type,
                image=image,
                texte=texte,
                message=message,
                retry_action_originale=retry,
                exclure_fenetre=exclure,
                priorite=priorite,
                categorie=category,
            )
            erreurs.append(erreur)

        return erreurs

    def _extract_priorite(self, block: str) -> int:
        """Extrait la priorité d'un bloc de définition d'erreur."""
        match = re.search(r"priorite\s*=\s*(\d+)", block)
        return int(match.group(1)) if match else 0

    def _extract_exclure_fenetre(self, block: str) -> int:
        """Extrait la durée d'exclusion d'un bloc de définition."""
        match = re.search(r"exclure_fenetre\s*=\s*(\w+)", block)
        if match:
            value = match.group(1)
            # Si c'est une constante comme EXCLUSION_COMPTE_UTILISE
            if value.isdigit():
                return int(value)
            # Valeur par défaut pour EXCLUSION_COMPTE_UTILISE (2h)
            if "EXCLUSION" in value:
                return 7200
        return 0


# Singleton
_erreur_service: ErreurService | None = None


def get_erreur_service() -> ErreurService:
    """Retourne l'instance singleton du service erreur."""
    global _erreur_service
    if _erreur_service is None:
        _erreur_service = ErreurService()
    return _erreur_service
