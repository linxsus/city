"""Générateur de code pour les états."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from ..config import GENERATED_DIR
from ..models.schemas import EtatSchema


class EtatGenerator:
    """Génère le code Python pour les classes Etat."""

    def __init__(self):
        templates_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.template = self.env.get_template("etat.py.j2")
        self.output_dir = GENERATED_DIR / "etats"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, etat: EtatSchema) -> str:
        """
        Génère le code Python pour un état.

        Args:
            etat: Schéma de l'état à générer

        Returns:
            Code Python généré
        """
        return self.template.render(
            nom_classe=etat.nom_classe,
            nom=etat.nom,
            groupes=etat.groupes,
            priorite=etat.priorite,
            methode_verif=etat.methode_verif.value,
            template_path=etat.template_path,
            texte_ocr=etat.texte_ocr,
            threshold=etat.threshold,
            description=etat.description or "",
        )

    def save(self, etat: EtatSchema) -> Path:
        """
        Sauvegarde le code généré dans un fichier.

        Args:
            etat: Schéma de l'état

        Returns:
            Chemin du fichier créé
        """
        code = self.generate(etat)
        filename = f"etat_{etat.nom}.py"
        filepath = self.output_dir / filename
        filepath.write_text(code, encoding="utf-8")

        # Mettre à jour le schéma avec le chemin du fichier
        etat.fichier_genere = str(filepath)

        return filepath

    def preview(self, etat: EtatSchema) -> dict:
        """
        Génère une prévisualisation du code.

        Args:
            etat: Schéma de l'état

        Returns:
            Dict avec le code et les métadonnées
        """
        code = self.generate(etat)
        filename = f"etat_{etat.nom}.py"

        return {
            "filename": filename,
            "code": code,
            "class_name": etat.nom_classe,
            "output_path": str(self.output_dir / filename),
        }
