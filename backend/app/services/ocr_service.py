"""
OCR Service - handles Scanned PDFs using pdf2image, OpenCV, and EasyOCR.
"""
import logging
import os
import tempfile
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class OCRService:
    def __init__(self):
        try:
            import easyocr
            # Initialize OCR reader (downloads model on first run if not cached)
            self.reader = easyocr.Reader(['en'], gpu=False)
        except ImportError:
            logger.error("EasyOCR not installed!")
            self.reader = None

    def extract_tables_from_scanned_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Convert scanned PDF to images, preprocess with OpenCV, and run EasyOCR.
        Reconstructs timetable grids.
        """
        logger.info(f"Starting OCR Pipeline for {file_path}")
        if not self.reader:
            return {"tables": [], "page_count": 0, "text": [], "method": "ocr_failed"}

        try:
            from pdf2image import convert_from_path
            import cv2
            import numpy as np

            # Convert PDF pages to images
            images = convert_from_path(file_path, dpi=200)
            page_count = len(images)
            all_tables = []
            all_text = []

            for i, img in enumerate(images):
                # Convert PIL Image to OpenCV format
                img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                
                # Preprocess: thresholding to make text pop
                _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

                # EasyOCR returns list of (bbox, text, prob)
                results = self.reader.readtext(gray, paragraph=False)
                
                page_text = "\n".join([res[1] for res in results])
                all_text.append(page_text)

                # Reconstructing a perfect grid from raw OCR bounding boxes is incredibly complex.
                # Since OCR is explicitly listed as a fallback, we attempt a naive row reconstruction
                # based on the Y-coordinates of the bounding boxes.
                
                # Sort by Y first, then X
                results.sort(key=lambda x: (x[0][0][1] // 20, x[0][0][0]))
                
                table_grid = []
                current_row = []
                last_y = -1

                for bbox, text, prob in results:
                    y = bbox[0][1]
                    if last_y == -1 or abs(y - last_y) < 20: # Same row
                        current_row.append(text)
                    else:
                        if current_row:
                            table_grid.append(current_row)
                        current_row = [text]
                    last_y = y
                
                if current_row:
                    table_grid.append(current_row)
                    
                if table_grid:
                    all_tables.append(table_grid)

            logger.info(f"OCR extracted {len(all_tables)} tables from {page_count} pages.")
            return {
                "tables": all_tables,
                "page_count": page_count,
                "text": all_text,
                "method": "easyocr"
            }

        except Exception as e:
            logger.error(f"OCR Pipeline failed: {e}")
            return {"tables": [], "page_count": 0, "text": [], "method": "ocr_failed"}
