"""Générateur de code pour les erreurs."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from ..config import PROJECT_ROOT
from ..models.schemas import ErreurCreate


class ErreurGenerator:
    """Génère le code Python pour ajouter des erreurs à liste_erreurs.py."""

    def __init__(self):
        templates_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.erreurs_file = PROJECT_ROOT / "erreurs" / "liste_erreurs.py"

    def generate_erreur_code(self, erreur: ErreurCreate) -> str:
        """
        Génère le code Python pour définir une erreur.

        Args:
            erreur: Schéma de l'erreur à générer

        Returns:
            Code Python pour définir l'erreur
        """
        if erreur.type.value == "image":
            template = self._generate_image_erreur(erreur)
        elif erreur.type.value == "texte":
            template = self._generate_texte_erreur(erreur)
        else:
            template = self._generate_image_erreur(erreur)

        return template

    def _generate_image_erreur(self, erreur: ErreurCreate) -> str:
        """Génère le code pour une erreur image."""
        lines = [
            f'    # {erreur.message}',
            f'    erreurs["{erreur.nom}"] = ItemErreurImage(',
            f'        fenetre,',
            f'        image="{erreur.image}",',
            f'        message="{erreur.message}",',
        ]

        if erreur.action_correction:
            lines.append(f'        action_correction={erreur.action_correction},')

        lines.append(f'        retry_action_originale={erreur.retry_action_originale},')

        if erreur.exclure_fenetre > 0:
            lines.append(f'        exclure_fenetre={erreur.exclure_fenetre},')

        lines.append(f'        priorite={erreur.priorite},')
        lines.append('    )')

        return '\n'.join(lines)

    def _generate_texte_erreur(self, erreur: ErreurCreate) -> str:
        """Génère le code pour une erreur texte."""
        lines = [
            f'    # {erreur.message}',
            f'    erreurs["{erreur.nom}"] = ItemErreurTexte(',
            f'        fenetre,',
            f'        texte="{erreur.texte}",',
            f'        message="{erreur.message}",',
        ]

        if erreur.action_correction:
            lines.append(f'        action_correction={erreur.action_correction},')

        lines.append(f'        retry_action_originale={erreur.retry_action_originale},')

        if erreur.exclure_fenetre > 0:
            lines.append(f'        exclure_fenetre={erreur.exclure_fenetre},')

        lines.append(f'        priorite={erreur.priorite},')
        lines.append('    )')

        return '\n'.join(lines)

    def get_category_section_marker(self, categorie: str) -> str:
        """Retourne le marqueur de section pour une catégorie."""
        markers = {
            "connexion": "# ERREURS DE CONNEXION",
            "jeu": "# ERREURS DE JEU",
            "popup": "# POPUPS D'INFORMATION",
            "systeme": "# ERREURS SYSTÈME",
        }
        return markers.get(categorie, "# AUTRES ERREURS")

    def add_erreur_to_file(self, erreur: ErreurCreate) -> bool:
        """
        Ajoute une erreur au fichier liste_erreurs.py.

        Args:
            erreur: Erreur à ajouter

        Returns:
            True si ajout réussi
        """
        if not self.erreurs_file.exists():
            return False

        content = self.erreurs_file.read_text(encoding="utf-8")

        # Trouver la section appropriée
        section_marker = self.get_category_section_marker(erreur.categorie)
        erreur_code = self.generate_erreur_code(erreur)

        # Chercher l'endroit où insérer (avant "return erreurs")
        return_marker = "    return erreurs"
        if return_marker in content:
            # Insérer avant le return
            insertion_point = content.rfind(return_marker)
            new_content = (
                content[:insertion_point]
                + "\n"
                + erreur_code
                + "\n\n"
                + content[insertion_point:]
            )
            self.erreurs_file.write_text(new_content, encoding="utf-8")
            return True

        return False

    def preview(self, erreur: ErreurCreate) -> dict:
        """
        Génère une prévisualisation du code.

        Args:
            erreur: Schéma de l'erreur

        Returns:
            Dict avec le code et les métadonnées
        """
        code = self.generate_erreur_code(erreur)

        return {
            "code": code,
            "nom": erreur.nom,
            "type": erreur.type.value,
            "categorie": erreur.categorie,
        }
