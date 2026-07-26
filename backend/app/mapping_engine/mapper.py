"""
Core mapper - matches subject codes from timetable cells
to the subject master, then resolves faculty.
"""
import logging
from typing import List, Dict, Any, Optional

from app.mapping_engine.normalizer import normalize_faculty_name, clean_display_name

logger = logging.getLogger(__name__)


class TimetableMapper:
    """
    Maps extracted timetable grid cells to subject master entries,
    resolving faculty names for each cell.
    """

    def __init__(self, subject_master: List[Dict[str, Any]]):
        """
        Args:
            subject_master: List of dicts from SubjectMasterExtractor.extract().
        """
        # Build a lookup by subject code (normalized lowercase)
        self.lookup = {}
        for entry in subject_master:
            code = entry.get("subject_code", "").strip().upper()
            if code:
                self.lookup[code] = entry

        logger.info(
            f"Mapper initialized with {len(self.lookup)} subject codes"
        )

    def map_cells(
        self, cells: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Map each extracted timetable cell to its subject and faculty.

        Args:
            cells: List of dicts from GridExtractor.extract_cells().

        Returns:
            List of enriched dicts with faculty_names, subject_name added.
        """
        mapped = []
        import re
        for cell in cells:
            raw_code = cell.get("subject_code", "").strip().upper()
            
            # Split combined subject codes (e.g., "CS2V68/CS2V25/CS2V23")
            parts = [p.strip() for p in re.split(r'[/,\|]+', raw_code) if p.strip()]
            if not parts:
                parts = [""]

            for code in parts:
                # Remove anything in parentheses at the end e.g., (L), (T), (LAB)
                code = re.sub(r'\s*\([A-Z]*\)\s*$', '', code)
                
                # Remove any lingering trailing non-alphanumeric characters
                code = re.sub(r'[^A-Z0-9\s]+$', '', code)
                
                # Handle LAB suffix for O(1) lookup
                lookup_code = code.replace(" LAB", "").strip()
                master_entry = self.lookup.get(lookup_code)

                # Ultimate Fallback: Check if the extracted code STARTS WITH any known subject code.
                if not master_entry:
                    best_match = ""
                    for master_code in self.lookup.keys():
                        if lookup_code.startswith(master_code) and len(master_code) > len(best_match):
                            best_match = master_code
                    
                    if best_match:
                        master_entry = self.lookup.get(best_match)
                        code = best_match

                enriched = {
                    **cell,
                    "subject_code": code if code else raw_code,
                    "subject_name": "",
                    "faculty_names": [],
                    "department": "",
                    "hours": None,
                    "validation_status": "valid",
                    "validation_message": None,
                }

                if master_entry:
                    enriched["subject_name"] = master_entry.get("subject_name", "")
                    faculty = [
                        clean_display_name(n)
                        for n in master_entry.get("faculty_names", [])
                        if n.strip()
                    ]
                    enriched["faculty_names"] = faculty
                    enriched["department"] = master_entry.get("department", "")
                    enriched["hours"] = master_entry.get("hours")

                    if not faculty:
                        enriched["validation_status"] = "warning"
                        enriched["validation_message"] = f"Missing faculty name in Master Table for subject '{code}'"

                else:
                    # Subject code not found in master
                    if code:
                        enriched["validation_status"] = "error"
                        enriched["validation_message"] = (
                            f"Subject code '{code}' not found in subject master table (Possible extraction error)"
                        )
                    else:
                        enriched["validation_status"] = "error"
                        enriched["validation_message"] = "Missing subject code from timetable cell"

                mapped.append(enriched)

        logger.info(
            f"Mapped {len(mapped)} cells, "
            f"{sum(1 for m in mapped if m['validation_status'] == 'valid')} valid, "
            f"{sum(1 for m in mapped if m['validation_status'] != 'valid')} issues"
        )
        return mapped
