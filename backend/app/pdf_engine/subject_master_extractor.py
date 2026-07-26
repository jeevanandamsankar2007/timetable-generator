"""
Subject master table extractor - reads the legend/reference table
from a timetable PDF and extracts subject code → name + faculty mappings.
"""
import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class SubjectMasterExtractor:
    """
    Extracts the subject master (legend) table that maps
    subject codes to full names and assigned faculty.
    """

    def extract(self, table: List[List[str]]) -> List[Dict[str, Any]]:
        """
        Parse a subject master table using pandas for robust cleaning.
        """
        import pandas as pd
        if not table or len(table) < 2:
            return []

        # Replace newlines with spaces and multiple spaces with a single space to help matching
        header = [re.sub(r'\s+', ' ', (cell or "").strip().lower().replace('\n', ' ')) for cell in table[0]]
        col_map = self._detect_columns(header)

        if col_map.get("code") is None:
            logger.warning("Could not detect subject code column in master table")
            return []

        df = pd.DataFrame(table[1:])
        
        # Replace empty strings with NA to use ffill where applicable (e.g., merged subject names)
        # Note: We won't forward fill faculty because it might just be empty.
        df.replace('', pd.NA, inplace=True)
        
        # Forward fill code and name in case of vertically merged cells across multiple faculty
        if col_map.get("code") is not None and col_map["code"] < len(df.columns):
            df[col_map["code"]] = df[col_map["code"]].ffill()
        if col_map.get("name") is not None and col_map["name"] < len(df.columns):
            df[col_map["name"]] = df[col_map["name"]].ffill()

        results = []
        debug_log = []
        
        for _, row in df.iterrows():
            if row.isna().all():
                continue
                
            raw_row = [str(x) if pd.notna(x) else "" for x in row]
            
            code = str(row.iloc[col_map["code"]]).strip() if pd.notna(row.iloc[col_map.get("code", -1)]) else ""
            if not code or code.lower() == 'nan':
                continue
                
            code = code.upper()

            # Strict Regex Validation to block garbage text like "K" or "M M"
            # Allow dashes, slashes and a broader range of alphanumeric structures
            if not re.match(r"^[A-Z0-9][A-Z0-9\s\-\/]{1,15}[A-Z0-9]$", code) or len(code) < 3:
                logger.warning(f"Rejected invalid Subject Code in Master Table: '{code}'. Raw Row: {row.to_dict()}")
                debug_log.append({
                    "raw_row": raw_row,
                    "extracted_code": code,
                    "extracted_subject": "",
                    "extracted_faculty": [],
                    "validation_status": "Invalid Subject Code (Regex Failed)"
                })
                continue

            name = str(row.iloc[col_map["name"]]).strip() if "name" in col_map and pd.notna(row.iloc[col_map["name"]]) else ""
            faculty_raw = str(row.iloc[col_map["faculty"]]).strip() if "faculty" in col_map and pd.notna(row.iloc[col_map["faculty"]]) else ""
            dept = str(row.iloc[col_map["department"]]).strip() if "department" in col_map and pd.notna(row.iloc[col_map["department"]]) else ""
            hours_str = str(row.iloc[col_map["hours"]]).strip() if "hours" in col_map and pd.notna(row.iloc[col_map["hours"]]) else ""

            if name.lower() == 'nan': name = ""
            if faculty_raw.lower() == 'nan': faculty_raw = ""

            hours = None
            if hours_str and hours_str.lower() != 'nan':
                nums = re.findall(r"\d+", hours_str)
                if nums:
                    hours = int(nums[0])

            faculty_names = self._split_faculty(faculty_raw)
            
            status = "Valid"
            if not faculty_names:
                status = "Missing Faculty"

            debug_log.append({
                "raw_row": raw_row,
                "extracted_code": code,
                "extracted_subject": name,
                "extracted_faculty": faculty_names,
                "validation_status": status
            })

            # Instead of ignoring, we add it so mapper can flag it as warning
            if not faculty_names:
                logger.warning(f"Extracted Master Table row with missing faculty for code '{code}'")

            results.append({
                "subject_code": code,
                "subject_name": name,
                "faculty_names": faculty_names,
                "department": dept,
                "hours": hours,
            })

        logger.info("=== SUBJECT MASTER PREVIEW ===")
        for res in results:
            logger.info(f"[{res['subject_code']}] -> {res['subject_name']} -> {res['faculty_names']}")
        logger.info("==============================")

        if not results:
            raise ValueError("Zero valid subject codes found in the Subject Master table.")
            
        logger.info(f"Extracted {len(results)} valid subjects from master table")
        return results, debug_log

    def _detect_columns(self, header: List[str]) -> Dict[str, int]:
        """Detect column positions from header keywords."""
        col_map = {}
        keywords = {
            "code": ["code", "sub code", "subject code", "course code", "abbr"],
            "name": ["name", "subject name", "subject", "course", "title"],
            "faculty": ["faculty", "staff", "teacher", "instructor", "handled by"],
            "department": ["dept", "department", "branch"],
            "hours": ["hour", "hours", "hrs", "credit", "l-t-p"],
        }

        for col_idx, cell in enumerate(header):
            for key, patterns in keywords.items():
                if key not in col_map:
                    for pattern in patterns:
                        if pattern in cell:
                            col_map[key] = col_idx
                            break

        return col_map

    def _safe_get(self, row: List[str], idx: int = None) -> str:
        """Safely get a cell value from a row."""
        if idx is None or idx >= len(row):
            return ""
        return (row[idx] or "").strip()

    def _split_faculty(self, raw: str) -> List[str]:
        """
        Split a faculty string that may contain multiple names.
        Handles separators: comma, slash, ampersand, newline, 'and'.
        """
        if not raw:
            return []

        # Split on common delimiters
        parts = re.split(r"[,/&\n]|\band\b", raw)
        names = []
        for part in parts:
            cleaned = part.strip()
            if cleaned and len(cleaned) > 1:
                names.append(cleaned)

        return names
