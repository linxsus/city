"""Moteur OCR avec EasyOCR et Tesseract (fallback)"""

import numpy as np
from PIL import Image

from utils.config import OCR_LANGUAGES, TESSERACT_CMD, USE_EASYOCR
from utils.logger import get_module_logger

logger = get_module_logger("OCREngine")

# Mapping des codes de langue : EasyOCR (2 lettres) → Tesseract (3 lettres)
LANG_MAPPING_TO_TESSERACT = {
    "fr": "fra",
    "en": "eng",
    "de": "deu",
    "es": "spa",
    "it": "ita",
    "pt": "por",
    "nl": "nld",
    "pl": "pol",
    "ru": "rus",
    "ja": "jpn",
    "ko": "kor",
    "zh": "chi_sim",
    "ar": "ara",
}

# Import conditionnel
try:
    import easyocr

    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    logger.warning("EasyOCR non disponible, utilisation de Tesseract")

try:
    import pytesseract

    # Configurer le chemin Tesseract si spécifié
    if TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("Tesseract non disponible")


class OCREngine:
    """Moteur OCR utilisant EasyOCR (par défaut) ou Tesseract (fallback)

    EasyOCR est plus précis mais plus lent.
    Tesseract est plus rapide mais moins précis.
    """

    def __init__(self, languages=None, use_easyocr=None):
        """
        Args:
            languages: Liste de langues (format EasyOCR: 2 lettres, ex: ['fr', 'en'])
            use_easyocr: Forcer EasyOCR (True) ou Tesseract (False)
        """
        self.languages = languages or OCR_LANGUAGES

        # Déterminer quel moteur utiliser
        if use_easyocr is None:
            use_easyocr = USE_EASYOCR

        self.use_easyocr = use_easyocr and EASYOCR_AVAILABLE

        # Initialiser le reader EasyOCR (lazy loading)
        self._reader = None

        if self.use_easyocr:
            logger.info(f"OCR: EasyOCR avec langues {self.languages}")
        elif TESSERACT_AVAILABLE:
            tesseract_langs = self._get_tesseract_languages()
            logger.info(f"OCR: Tesseract avec langues {tesseract_langs}")
        else:
            logger.error("Aucun moteur OCR disponible!")

    def _get_tesseract_languages(self):
        """Convertit les codes de langue EasyOCR vers Tesseract (PROTÉGÉ)

        Returns:
            str: Chaîne de langues format Tesseract (ex: 'fra+eng')
        """
        tesseract_langs = []
        for lang in self.languages:
            if lang in LANG_MAPPING_TO_TESSERACT:
                tesseract_langs.append(LANG_MAPPING_TO_TESSERACT[lang])
            else:
                # Si pas de mapping, essayer le code tel quel
                tesseract_langs.append(lang)
                logger.warning(f"Pas de mapping Tesseract pour '{lang}', utilisation directe")

        return "+".join(tesseract_langs)

    @property
    def reader(self):
        """Lazy initialization du reader EasyOCR"""
        if self._reader is None and self.use_easyocr:
            logger.info("Initialisation EasyOCR (peut prendre quelques secondes)...")
            self._reader = easyocr.Reader(self.languages, gpu=True)
            logger.info("EasyOCR initialisé")
        return self._reader

    def _to_numpy(self, image):
        """Convertit une image en numpy array RGB (PROTÉGÉ)

        Args:
            image: PIL.Image ou numpy.ndarray

        Returns:
            numpy.ndarray: Image RGB
        """
        if isinstance(image, Image.Image):
            return np.array(image)
        return image

    def _to_pil(self, image):
        """Convertit une image en PIL.Image (PROTÉGÉ)

        Args:
            image: PIL.Image ou numpy.ndarray

        Returns:
            PIL.Image
        """
        if isinstance(image, np.ndarray):
            return Image.fromarray(image)
        return image

    def _apply_region(self, image, region):
        """Applique une région de découpe (PROTÉGÉ)

        Args:
            image: Image source
            region: Tuple (x, y, width, height) ou None

        Returns:
            Image découpée et offset (offset_x, offset_y)
        """
        if region is None:
            return image, 0, 0

        x, y, w, h = region

        if isinstance(image, Image.Image):
            cropped = image.crop((x, y, x + w, y + h))
        else:
            cropped = image[y : y + h, x : x + w]

        return cropped, x, y

    def extract_text(self, image, region=None):
        """Extrait tout le texte d'une image

        Args:
            image: PIL.Image ou numpy.ndarray
            region: Région optionnelle (x, y, width, height)

        Returns:
            str: Texte extrait
        """
        image, _, _ = self._apply_region(image, region)

        try:
            if self.use_easyocr:
                img_array = self._to_numpy(image)
                results = self.reader.readtext(img_array)
                text = " ".join([result[1] for result in results])
            elif TESSERACT_AVAILABLE:
                pil_image = self._to_pil(image)
                lang_str = self._get_tesseract_languages()
                text = pytesseract.image_to_string(pil_image, lang=lang_str)
            else:
                logger.error("Aucun moteur OCR disponible")
                return ""

            return text.strip()

        except Exception as e:
            logger.error(f"Erreur extract_text: {e}")
            return ""

    def find_text(self, image, search_text, region=None, case_sensitive=False):
        """Vérifie si un texte est présent dans l'image

        Args:
            image: PIL.Image ou numpy.ndarray
            search_text: Texte à chercher
            region: Région optionnelle (x, y, width, height)
            case_sensitive: Sensible à la casse

        Returns:
            bool: True si le texte est trouvé
        """
        text = self.extract_text(image, region)

        if not case_sensitive:
            return search_text.lower() in text.lower()
        return search_text in text

    def find_text_position(self, image, search_text, region=None, case_sensitive=False):
        """Trouve la position d'un texte dans l'image

        Args:
            image: PIL.Image ou numpy.ndarray
            search_text: Texte à chercher
            region: Région optionnelle (x, y, width, height)
            case_sensitive: Sensible à la casse

        Returns:
            Tuple (x, y) ou None: Centre du texte trouvé
        """
        image, offset_x, offset_y = self._apply_region(image, region)

        try:
            if self.use_easyocr:
                return self._find_text_position_easyocr(
                    image, search_text, offset_x, offset_y, case_sensitive
                )
            elif TESSERACT_AVAILABLE:
                return self._find_text_position_tesseract(
                    image, search_text, offset_x, offset_y, case_sensitive
                )
            else:
                return None

        except Exception as e:
            logger.error(f"Erreur find_text_position: {e}")
            return None

    def _find_text_position_easyocr(self, image, search_text, offset_x, offset_y, case_sensitive):
        """Trouve la position avec EasyOCR (PROTÉGÉ)"""
        img_array = self._to_numpy(image)
        results = self.reader.readtext(img_array)

        search = search_text if case_sensitive else search_text.lower()

        for bbox, text, _conf in results:
            text_compare = text if case_sensitive else text.lower()

            if search in text_compare:
                # Calculer le centre du bounding box
                points = np.array(bbox)
                center_x = int(np.mean(points[:, 0])) + offset_x
                center_y = int(np.mean(points[:, 1])) + offset_y

                logger.debug(f"Texte '{search_text}' trouvé à ({center_x}, {center_y})")
                return (center_x, center_y)

        return None

    def _find_text_position_tesseract(self, image, search_text, offset_x, offset_y, case_sensitive):
        """Trouve la position avec Tesseract (PROTÉGÉ)"""
        pil_image = self._to_pil(image)
        lang_str = self._get_tesseract_languages()

        data = pytesseract.image_to_data(
            pil_image, lang=lang_str, output_type=pytesseract.Output.DICT
        )

        search = search_text if case_sensitive else search_text.lower()

        for i, text in enumerate(data["text"]):
            if not text.strip():
                continue

            text_compare = text if case_sensitive else text.lower()

            if search in text_compare:
                x = data["left"][i] + data["width"][i] // 2 + offset_x
                y = data["top"][i] + data["height"][i] // 2 + offset_y

                logger.debug(f"Texte '{search_text}' trouvé à ({x}, {y})")
                return (x, y)

        return None

    def extract_all_text_with_positions(self, image, region=None):
        """Extrait tous les textes avec leurs positions

        Args:
            image: PIL.Image ou numpy.ndarray
            region: Région optionnelle

        Returns:
            List[Dict]: Liste de {'text': str, 'position': (x, y), 'confidence': float}
        """
        image, offset_x, offset_y = self._apply_region(image, region)

        results = []

        try:
            if self.use_easyocr:
                img_array = self._to_numpy(image)
                ocr_results = self.reader.readtext(img_array)

                for bbox, text, conf in ocr_results:
                    if text.strip():
                        points = np.array(bbox)
                        center_x = int(np.mean(points[:, 0])) + offset_x
                        center_y = int(np.mean(points[:, 1])) + offset_y

                        results.append(
                            {"text": text, "position": (center_x, center_y), "confidence": conf}
                        )

            elif TESSERACT_AVAILABLE:
                pil_image = self._to_pil(image)
                lang_str = self._get_tesseract_languages()

                data = pytesseract.image_to_data(
                    pil_image, lang=lang_str, output_type=pytesseract.Output.DICT
                )

                for i, text in enumerate(data["text"]):
                    if text.strip():
                        x = data["left"][i] + data["width"][i] // 2 + offset_x
                        y = data["top"][i] + data["height"][i] // 2 + offset_y
                        conf = float(data["conf"][i]) / 100 if data["conf"][i] != -1 else 0

                        results.append({"text": text, "position": (x, y), "confidence": conf})

        except Exception as e:
            logger.error(f"Erreur extract_all_text_with_positions: {e}")

        return results


# Instance globale (lazy)
_ocr_engine_instance = None


def get_ocr_engine():
    """Retourne une instance singleton de OCREngine

    Returns:
        OCREngine: Instance partagée
    """
    global _ocr_engine_instance
    if _ocr_engine_instance is None:
        _ocr_engine_instance = OCREngine()
    return _ocr_engine_instance
