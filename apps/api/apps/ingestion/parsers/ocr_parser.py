import io
import logging

from PIL import Image

from .normalization import normalize_text

logger = logging.getLogger(__name__)


class OCRParser:
    """Adapter for optical character recognition (OCR) on scanned documents or images.

    Designed to gracefully handle environments where Tesseract binary might not
    be installed, while executing OCR when libraries are present.
    """

    def __init__(self, default_lang: str = "fra+eng"):
        self.default_lang = default_lang
        self._tesseract_available: bool | None = None

    def is_available(self) -> bool:
        """Checks if pytesseract and Tesseract OCR engine are available."""
        if self._tesseract_available is not None:
            return self._tesseract_available

        try:
            import pytesseract

            # Attempt a probe
            pytesseract.get_tesseract_version()
            self._tesseract_available = True
        except Exception:
            self._tesseract_available = False

        return self._tesseract_available

    def parse_image_bytes(self, image_bytes: bytes, lang: str | None = None) -> str:
        """Extracts text from raw image bytes using OCR."""
        if not image_bytes:
            return ""

        try:
            image = Image.open(io.BytesIO(image_bytes))
            return self.parse_image(image, lang=lang)
        except Exception as e:
            logger.warning(f"[OCRParser] Failed to parse image bytes: {e}")
            return ""

    def parse_image(self, image: Image.Image, lang: str | None = None) -> str:
        """Extracts text from a PIL Image instance."""
        target_lang = lang or self.default_lang

        if not self.is_available():
            logger.info("[OCRParser] Tesseract OCR is not installed or available on this system.")
            return ""

        try:
            import pytesseract

            raw_text = pytesseract.image_to_string(image, lang=target_lang)
            return normalize_text(raw_text)
        except Exception as e:
            logger.error(f"[OCRParser] OCR processing failed: {e}")
            return ""

    def process_page_image_if_needed(
        self,
        text: str,
        image_bytes: bytes | None = None,
        min_char_threshold: int = 40,
    ) -> tuple[str, bool]:
        """If extracted text is below min_char_threshold and image_bytes are provided,

        attempts OCR extraction. Returns (final_text, ocr_used).
        """
        clean_text = normalize_text(text)
        if len(clean_text) >= min_char_threshold or not image_bytes:
            return clean_text, False

        ocr_text = self.parse_image_bytes(image_bytes)
        if ocr_text:
            return ocr_text, True

        return clean_text, False
