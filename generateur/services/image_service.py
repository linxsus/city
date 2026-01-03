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

    def compute_dhash(self, image_path: str | Path, hash_size: int = 8) -> str:
        """
        Calcule un hash perceptuel (dHash) de l'image.

        dHash compare les pixels adjacents pour créer un hash robuste
        aux changements de taille, contraste et couleur.

        Args:
            image_path: Chemin de l'image
            hash_size: Taille du hash (8 = 64 bits)

        Returns:
            Hash hexadécimal de l'image
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image non trouvée: {image_path}")

        with Image.open(path) as img:
            # Convertir en niveaux de gris
            img_gray = img.convert("L")
            # Redimensionner à hash_size+1 x hash_size
            img_small = img_gray.resize(
                (hash_size + 1, hash_size), Image.Resampling.LANCZOS
            )

            # Comparer chaque pixel avec son voisin de droite
            pixels = list(img_small.getdata())
            diff = []
            for row in range(hash_size):
                for col in range(hash_size):
                    left = pixels[row * (hash_size + 1) + col]
                    right = pixels[row * (hash_size + 1) + col + 1]
                    diff.append(left > right)

            # Convertir en hexadécimal
            decimal_value = sum([2**i for i, v in enumerate(diff) if v])
            return f"{decimal_value:016x}"

    def compute_hash(self, image_path: str | Path) -> str:
        """
        Calcule un hash de l'image pour détection de duplicatas.
        Alias vers compute_dhash pour compatibilité.

        Args:
            image_path: Chemin de l'image

        Returns:
            Hash hexadécimal de l'image
        """
        return self.compute_dhash(image_path)

    def hamming_distance(self, hash1: str, hash2: str) -> int:
        """
        Calcule la distance de Hamming entre deux hashes.

        Args:
            hash1: Premier hash hexadécimal
            hash2: Deuxième hash hexadécimal

        Returns:
            Nombre de bits différents
        """
        if len(hash1) != len(hash2):
            return 64  # Maximum distance

        # Convertir en entiers et compter les bits différents
        int1 = int(hash1, 16)
        int2 = int(hash2, 16)
        xor = int1 ^ int2
        return bin(xor).count("1")

    def find_similar_templates(
        self,
        image_path: str | Path,
        threshold: float = 0.9,
        include_framework: bool = True,
    ) -> list[dict]:
        """
        Trouve les templates similaires à une image.

        Args:
            image_path: Chemin de l'image à comparer
            threshold: Seuil de similarité (0-1)
            include_framework: Inclure les templates du framework

        Returns:
            Liste de dicts avec path, relative_path, similarity, source
        """
        similar = []

        try:
            new_hash = self.compute_dhash(image_path)
        except Exception as e:
            print(f"Erreur lors du calcul du hash: {e}")
            return []

        # Templates générés
        if self.templates_dir.exists():
            for template_path in self.templates_dir.rglob("*.png"):
                try:
                    existing_hash = self.compute_dhash(template_path)
                    distance = self.hamming_distance(new_hash, existing_hash)
                    # Distance 0 = identique, 64 = complètement différent
                    similarity = 1 - (distance / 64)

                    if similarity >= threshold:
                        similar.append({
                            "path": str(template_path),
                            "relative_path": template_path.name,
                            "similarity": round(similarity, 3),
                            "source": "generated",
                        })
                except Exception:
                    continue

        # Templates du framework
        if include_framework and self.framework_templates_dir.exists():
            for template_path in self.framework_templates_dir.rglob("*.png"):
                try:
                    existing_hash = self.compute_dhash(template_path)
                    distance = self.hamming_distance(new_hash, existing_hash)
                    similarity = 1 - (distance / 64)

                    if similarity >= threshold:
                        rel_path = str(
                            template_path.relative_to(self.framework_templates_dir)
                        )
                        similar.append({
                            "path": str(template_path),
                            "relative_path": rel_path,
                            "similarity": round(similarity, 3),
                            "source": "framework",
                        })
                except Exception:
                    continue

        similar.sort(key=lambda x: x["similarity"], reverse=True)
        return similar

    def find_duplicates(
        self,
        image_path: str | Path,
        exact_threshold: float = 0.95,
        similar_threshold: float = 0.85,
    ) -> dict:
        """
        Trouve les duplicatas et templates similaires à une image.

        Args:
            image_path: Chemin de l'image à comparer
            exact_threshold: Seuil pour considérer un duplicata exact
            similar_threshold: Seuil pour considérer un template similaire

        Returns:
            Dict avec exact_duplicates, similar_templates, is_duplicate
        """
        all_similar = self.find_similar_templates(
            image_path,
            threshold=similar_threshold,
            include_framework=True,
        )

        exact_duplicates = [t for t in all_similar if t["similarity"] >= exact_threshold]
        similar_templates = [
            t for t in all_similar
            if t["similarity"] < exact_threshold
        ]

        return {
            "is_duplicate": len(exact_duplicates) > 0,
            "exact_duplicates": exact_duplicates,
            "similar_templates": similar_templates,
            "checked_image": str(image_path),
        }

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
