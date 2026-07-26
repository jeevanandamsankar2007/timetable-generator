"""
PDF Detection Service - determines whether a PDF is Digital (Text) or Scanned (Image).
"""
import logging
import fitz

logger = logging.getLogger(__name__)


class PDFDetectionService:
    @staticmethod
    def is_scanned_pdf(file_path: str) -> bool:
        """
        Detect if a PDF is a scanned image instead of a digital text document.
        Returns True if scanned, False if digital.
        """
        try:
            doc = fitz.open(file_path)
            if len(doc) == 0:
                return False

            total_text = ""
            # Check up to first 3 pages to be safe
            for i in range(min(3, len(doc))):
                total_text += doc[i].get_text("text").strip()
            
            # If there's barely any text, it's highly likely to be a scanned image
            if len(total_text) < 100:
                logger.info(f"PDF {file_path} detected as SCANNED (only {len(total_text)} text chars).")
                return True
                
            logger.info(f"PDF {file_path} detected as DIGITAL ({len(total_text)} text chars on first {min(3, len(doc))} pages).")
            return False

        except Exception as e:
            logger.error(f"Error detecting PDF type for {file_path}: {e}")
            # Default to digital if detection fails to avoid heavy OCR overhead
            return False
