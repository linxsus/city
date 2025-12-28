"""Service de traitement d'images."""

import hashlib
import shutil
import uuid
from pathlib import Path

from PIL import Image

from ..config import (
    FRAMEWORK_TEMPLATES_DIR,
    GENERATED_DIR,
    TEMPLATES_OUTPUT_DIR,
    UPLOAD_DIR,
)
from ..models.schemas import RegionSchema


class ImageService:
    """Service pour le traitement et la gestion des images."""

    def __init__(self):
        self.upload_dir = UPLOAD_DIR
        self.templates_dir = TEMPLATES_OUTPUT_DIR
        self.generated_dir = GENERATED_DIR
        self.framework_templates_dir = FRAMEWORK_TEMPLATES_DIR

    def save_upload(self, file_content: bytes, filename: str) -> Path:
        """
        Sauvegarde un fichier uploadé.

        Args:
            file_content: Contenu binaire du fichier
            filename: Nom original du fichier

        Returns:
            Chemin du fichier sauvegardé
        """
        # Générer un nom unique
        ext = Path(filename).suffix.lower()
        if ext not in [".png", ".jpg", ".jpeg"]:
            ext = ".png"

        unique_name = f"{uuid.uuid4().hex}{ext}"
        save_path = self.upload_dir / unique_name

        with open(save_path, "wb") as f:
            f.write(file_content)

        return save_path

    def get_image_info(self, image_path: str | Path) -> dict:
        """
        Récupère les informations d'une image.

        Args:
            image_path: Chemin de l'image

        Returns:
            Dict avec width, height, format, size
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image non trouvée: {image_path}")

        with Image.open(path) as img:
            return {
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode,
                "size_bytes": path.stat().st_size,
            }

    def crop_region(
        self,
        image_path: str | Path,
        region: RegionSchema,
        output_name: str | None = None,
        output_subdir: str | None = None,
    ) -> Path:
        """
        Découpe une région d'une image et la sauvegarde comme template.

        Args:
            image_path: Chemin de l'image source
            region: Région à découper
            output_name: Nom du fichier de sortie (sans extension)
            output_subdir: Sous-dossier dans templates/ (si spécifié, sauvegarde dans framework)

        Returns:
            Chemin du template créé
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image non trouvée: {image_path}")

        # Déterminer le dossier de sortie
        # Si un sous-dossier est spécifié, on sauvegarde dans le framework templates
        if output_subdir:
            output_dir = self.framework_templates_dir / output_subdir
        else:
            output_dir = self.templates_dir

        output_dir.mkdir(parents=True, exist_ok=True)

        # Nom du fichier
        if not output_name:
            output_name = f"template_{uuid.uuid4().hex[:8]}"

        output_path = output_dir / f"{output_name}.png"

        # Découper et sauvegarder
        with Image.open(path) as img:
            box = (
                region.x,
                region.y,
                region.x + region.width,
                region.y + region.height,
            )

            # Vérifier les limites
            if box[2] > img.width or box[3] > img.height:
                raise ValueError(
                    f"Région hors limites: image={img.width}x{img.height}, "
                    f"région={region.x},{region.y} -> {box[2]},{box[3]}"
                )

            cropped = img.crop(box)
            cropped.save(output_path, "PNG")

        return output_path

    def compute_hash(self, image_path: str | Path) -> str:
        """
        Calcule un hash de l'image pour détection de duplicatas.

        Args:
            image_path: Chemin de l'image

        Returns:
            Hash hexadécimal de l'image
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image non trouvée: {image_path}")

        # Hash basé sur le contenu redimensionné (robuste aux variations mineures)
        with Image.open(path) as img:
            # Convertir en niveaux de gris et redimensionner
            img_gray = img.convert("L")
            img_small = img_gray.resize((16, 16), Image.Resampling.LANCZOS)

            # Hash du contenu
            pixels = list(img_small.getdata())
            return hashlib.md5(bytes(pixels)).hexdigest()

    def find_similar_templates(
        self,
        image_path: str | Path,
        threshold: float = 0.9,
    ) -> list[tuple[Path, float]]:
        """
        Trouve les templates similaires à une image.

        Args:
            image_path: Chemin de l'image à comparer
            threshold: Seuil de similarité (0-1)

        Returns:
            Liste de (chemin_template, score_similarité)
        """
        if not self.templates_dir.exists():
            return []

        new_hash = self.compute_hash(image_path)
        similar = []

        for template_path in self.templates_dir.rglob("*.png"):
            try:
                existing_hash = self.compute_hash(template_path)

                # Comparer les hashes (distance de Hamming simplifiée)
                diff = sum(a != b for a, b in zip(new_hash, existing_hash))
                similarity = 1 - (diff / len(new_hash))

                if similarity >= threshold:
                    similar.append((template_path, similarity))
            except Exception:
                continue

        similar.sort(key=lambda x: x[1], reverse=True)
        return similar

    def get_relative_template_path(self, template_path: Path) -> str:
        """
        Retourne le chemin relatif d'un template pour utilisation dans le code.

        Args:
            template_path: Chemin absolu du template

        Returns:
            Chemin relatif depuis le dossier templates
        """
        try:
            return str(template_path.relative_to(self.templates_dir))
        except ValueError:
            return template_path.name

    def cleanup_upload(self, image_path: str | Path) -> bool:
        """
        Supprime un fichier uploadé temporaire.

        Args:
            image_path: Chemin du fichier à supprimer

        Returns:
            True si supprimé, False sinon
        """
        path = Path(image_path)
        if path.exists() and path.is_relative_to(self.upload_dir):
            path.unlink()
            return True
        return False

    def copy_to_framework(
        self,
        template_path: Path,
        dest_subdir: str,
    ) -> Path:
        """
        Copie un template vers le dossier templates du framework.

        Args:
            template_path: Chemin du template à copier
            dest_subdir: Sous-dossier de destination

        Returns:
            Chemin de destination
        """
        from ..config import FRAMEWORK_TEMPLATES_DIR

        dest_dir = FRAMEWORK_TEMPLATES_DIR / dest_subdir
        dest_dir.mkdir(parents=True, exist_ok=True)

        dest_path = dest_dir / template_path.name
        shutil.copy2(template_path, dest_path)

        return dest_path


# Singleton
_image_service: ImageService | None = None


def get_image_service() -> ImageService:
    """Retourne l'instance singleton du service image."""
    global _image_service
    if _image_service is None:
        _image_service = ImageService()
    return _image_service
