"""Service de gestion des états."""

from pathlib import Path

from ..config import GENERATED_DIR, get_existing_groups, get_existing_states
from ..models.schemas import EtatCreate, EtatSchema, MethodeVerification, RegionSchema
from .image_service import get_image_service


def snake_to_pascal(name: str) -> str:
    """Convertit snake_case en PascalCase."""
    return "".join(word.capitalize() for word in name.split("_"))


class EtatService:
    """Service pour la création et gestion des états."""

    def __init__(self):
        self.image_service = get_image_service()
        self.etats_dir = GENERATED_DIR / "etats"
        self.etats_dir.mkdir(parents=True, exist_ok=True)

    def get_existing_groups(self) -> list[str]:
        """Récupère les groupes existants."""
        return get_existing_groups()

    def get_existing_states(self) -> list[str]:
        """Récupère les états existants."""
        return get_existing_states()

    def create_etat(
        self,
        data: EtatCreate,
        save_template: bool = True,
    ) -> EtatSchema:
        """
        Crée un nouvel état.

        Args:
            data: Données de l'état à créer
            save_template: Si True, découpe et sauvegarde le template

        Returns:
            EtatSchema complet avec les chemins générés
        """
        # Générer le nom de classe
        nom_classe = f"Etat{snake_to_pascal(data.nom)}"

        # Préparer le chemin du template
        template_path = None

        if data.methode_verif in [
            MethodeVerification.IMAGE,
            MethodeVerification.COMBINAISON,
        ]:
            if data.template_region and save_template:
                # Découper le template
                output_path = self.image_service.crop_region(
                    image_path=data.image_source,
                    region=data.template_region,
                    output_name=f"template_{data.nom}",
                    output_subdir=data.nom,
                )
                template_path = self.image_service.get_relative_template_path(
                    output_path
                )

        # Créer le schéma complet
        etat = EtatSchema(
            nom=data.nom,
            nom_classe=nom_classe,
            groupes=data.groupes,
            priorite=data.priorite,
            methode_verif=data.methode_verif,
            template_region=data.template_region,
            template_path=template_path,
            texte_ocr=data.texte_ocr,
            texte_region=data.texte_region,
            threshold=data.threshold,
            image_source=data.image_source,
            description=data.description,
        )

        return etat

    def validate_etat(self, data: EtatCreate) -> list[str]:
        """
        Valide les données d'un état.

        Args:
            data: Données à valider

        Returns:
            Liste des erreurs (vide si valide)
        """
        errors = []

        # Vérifier le nom
        existing_states = self.get_existing_states()
        if data.nom in existing_states:
            errors.append(f"Un état avec le nom '{data.nom}' existe déjà")

        # Vérifier la cohérence méthode/données
        if data.methode_verif == MethodeVerification.IMAGE:
            if not data.template_region:
                errors.append("Une région de template est requise pour la détection par image")

        elif data.methode_verif == MethodeVerification.TEXTE:
            if not data.texte_ocr:
                errors.append("Un texte OCR est requis pour la détection par texte")

        elif data.methode_verif == MethodeVerification.COMBINAISON:
            if not data.template_region:
                errors.append("Une région de template est requise pour la combinaison")
            if not data.texte_ocr:
                errors.append("Un texte OCR est requis pour la combinaison")

        # Vérifier l'image source
        if not Path(data.image_source).exists():
            errors.append(f"Image source non trouvée: {data.image_source}")

        return errors

    def check_duplicate_template(
        self,
        image_path: str | Path,
        region: RegionSchema,
    ) -> list[dict]:
        """
        Vérifie si un template similaire existe déjà.

        Args:
            image_path: Chemin de l'image source
            region: Région à vérifier

        Returns:
            Liste des templates similaires avec leur score
        """
        # Créer un fichier temporaire avec la région découpée
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            self.image_service.crop_region(
                image_path=image_path,
                region=region,
                output_name=tmp_path.stem,
                output_subdir=None,
            )

            similar = self.image_service.find_similar_templates(tmp_path)

            return [
                {
                    "path": str(path),
                    "similarity": score,
                }
                for path, score in similar
            ]
        finally:
            if tmp_path.exists():
                tmp_path.unlink()


# Singleton
_etat_service: EtatService | None = None


def get_etat_service() -> EtatService:
    """Retourne l'instance singleton du service état."""
    global _etat_service
    if _etat_service is None:
        _etat_service = EtatService()
    return _etat_service
