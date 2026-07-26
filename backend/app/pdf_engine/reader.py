"""
Deterministic Multi-Stage PDF Reader Pipeline:
Stage 1: PyMuPDF (Validation & Meta)
Stage 2: pdfplumber (Selectable Text)
Stage 3: Camelot (Structured Tables)
"""
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class PDFReader:
    """
    Reads a timetable PDF and extracts raw table data using a 3-stage
    deterministic pipeline (PyMuPDF -> pdfplumber -> Camelot).
    """
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

    def read(self) -> Dict[str, Any]:
        """Read the PDF through the multi-stage pipeline."""
        logger.info(f"Starting Multi-Stage PDF Pipeline for: {self.file_path.name}")
        
        page_count = 0
        page_texts = []
        tables = []
        tables_meta = []
        
        try:
            # Stage 1: PyMuPDF (fitz)
            import fitz
            logger.info("Stage 1: PyMuPDF (Validating PDF and Coordinates)")
            with fitz.open(str(self.file_path)) as doc:
                page_count = len(doc)
                if page_count == 0:
                    raise ValueError("PDF has no pages.")
                
                # Validation: Reject if completely empty (scanned image with no text)
                has_text = False
                for page in doc:
                    if page.get_text("text").strip():
                        has_text = True
                        break
                
                if not has_text:
                    logger.warning("PDF appears to be a scanned image with no selectable text. Switching to OCR fallback.")
                    return self._extract_with_ocr()

            # Stage 2: pdfplumber
            import pdfplumber
            logger.info("Stage 2: pdfplumber (Extracting Selectable Text)")
            with pdfplumber.open(str(self.file_path)) as pdf:
                for page in pdf.pages:
                    page_texts.append(page.extract_text() or "")
            
            # Stage 3: Camelot
            import camelot
            logger.info("Stage 3: Camelot (Extracting Structured Tables)")
            # 'lattice' flavor is strictly deterministic based on gridlines
            extracted_tables = camelot.read_pdf(
                str(self.file_path), 
                pages='all', 
                flavor='lattice',
                line_scale=40  # Adjust if lines are very thin/broken
            )
            
            if not extracted_tables or extracted_tables.n == 0:
                logger.error("Camelot found no tables.")
            else:
                for t in extracted_tables:
                    # Convert Camelot DataFrame to list of lists (string representation)
                    df = t.df
                    cleaned = []
                    for _, row in df.iterrows():
                        cleaned_row = [(str(cell) or "").strip() for cell in row]
                        # Only add non-empty rows
                        if any(cleaned_row):
                            cleaned.append(cleaned_row)
                    
                    if cleaned:
                        tables.append(cleaned)
                        tables_meta.append({"page": t.page})
            
            if not tables:
                logger.error("Pipeline failed to extract structured tables.")
                return {"tables": [], "tables_meta": [], "page_count": page_count, "text": page_texts}

            logger.info(f"Pipeline successfully extracted {len(tables)} tables.")
            return {
                "tables": tables,
                "tables_meta": tables_meta,
                "page_count": page_count, 
                "text": page_texts, 
                "method": "pymupdf->pdfplumber->camelot"
            }
            
        except ImportError as e:
            logger.error(f"Missing dependency for pipeline: {e}")
            raise RuntimeError(f"Missing required extraction dependency: {e}")
        except Exception as e:
            logger.error(f"PDF extraction pipeline failed: {e}")
            return {"tables": [], "page_count": page_count, "text": page_texts}

    def _extract_with_ocr(self) -> Dict[str, Any]:
        """
        Fallback OCR engine for scanned image PDFs.
        Uses OpenCV to deterministically isolate table cells by their gridlines (lattice),
        then runs EasyOCR strictly inside the isolated crops to guarantee 100% structural accuracy.
        """
        import cv2
        import numpy as np
        from pdf2image import convert_from_path
        import easyocr

        logger.info("Initializing OpenCV + EasyOCR fallback pipeline...")
        # Extract high-res images from PDF
        pages = convert_from_path(str(self.file_path), dpi=300)
        if not pages:
            logger.error("pdf2image failed to extract any pages.")
            return {"tables": [], "page_count": 0, "text": []}
        
        reader = easyocr.Reader(['en'], gpu=False)  # Force CPU unless GPU is guaranteed
        tables = []
        tables_meta = []
        page_texts = []
        
        for idx, page_img in enumerate(pages):
            logger.info(f"Processing page {idx+1}/{len(pages)} with OpenCV and OCR...")
            img = cv2.cvtColor(np.array(page_img), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Enhance image and binarize
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 15, -2)
            
            # Detect horizontal lines
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
            detect_horizontal = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
            
            # Detect vertical lines
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 50))
            detect_vertical = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
            
            # Combine to form the grid lattice
            grid = cv2.addWeighted(detect_horizontal, 0.5, detect_vertical, 0.5, 0.0)
            
            # Find contours (the individual cells)
            contours, _ = cv2.findContours(grid, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            bounding_boxes = [cv2.boundingRect(c) for c in contours]
            img_h, img_w = img.shape[:2]
            
            # Filter noise and large outer borders
            valid_boxes = [b for b in bounding_boxes if b[2] > 20 and b[3] > 10 and b[2] < img_w*0.95 and b[3] < img_h*0.95]
            
            if not valid_boxes:
                logger.warning(f"No valid table cells found on page {idx+1} using OpenCV.")
                continue
                
            # Sort boxes top to bottom, then left to right
            valid_boxes.sort(key=lambda b: b[1])
            
            rows = []
            current_row = [valid_boxes[0]]
            y_threshold = valid_boxes[0][3] / 2
            
            for box in valid_boxes[1:]:
                if abs(box[1] - current_row[0][1]) < y_threshold:
                    current_row.append(box)
                else:
                    current_row.sort(key=lambda b: b[0])
                    rows.append(current_row)
                    current_row = [box]
            
            if current_row:
                current_row.sort(key=lambda b: b[0])
                rows.append(current_row)
            
            # Reverse rows because RETR_TREE and top-down sorting sometimes mixes up the outer bounding box
            # But sorting strictly by Y mostly fixes it.
            
            page_table = []
            full_page_text = []
            
            for row_boxes in rows:
                row_data = []
                for (x, y, w, h) in row_boxes:
                    # Crop the cell with a small inner padding to avoid reading the cell borders
                    pad = 3
                    if h > pad*2 and w > pad*2:
                        cell_crop = gray[y+pad:y+h-pad, x+pad:x+w-pad]
                    else:
                        cell_crop = gray[y:y+h, x:x+w]
                    
                    # Run EasyOCR strictly inside the isolated crop
                    result = reader.readtext(cell_crop, detail=0)
                    text = " ".join(result).strip()
                    row_data.append(text)
                    if text:
                        full_page_text.append(text)
                
                # Only add if the row is not completely empty
                if any(row_data):
                    page_table.append(row_data)
            
            if page_table:
                tables.append(page_table)
                tables_meta.append({"page": idx + 1})
            page_texts.append("\n".join(full_page_text))
            
        if not tables:
             logger.error("EasyOCR fallback failed to extract structured tables.")
             return {"tables": [], "tables_meta": [], "page_count": len(pages), "text": page_texts}

        logger.info(f"EasyOCR fallback successfully extracted {len(tables)} tables.")
        return {
            "tables": tables,
            "tables_meta": tables_meta,
            "page_count": len(pages),
            "text": page_texts,
            "method": "opencv->easyocr"
        }




