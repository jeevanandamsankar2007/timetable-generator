"""
Grid extractor - parses a classified timetable grid into structured cell data.
"""
import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class GridExtractor:
    """
    Takes a raw timetable table and its detected structure,
    then extracts structured cell data for each day+period.
    """

    def __init__(self, table: List[List[str]], structure: Dict[str, Any]):
        self.table = table
        self.structure = structure

    def extract_cells(self) -> List[Dict[str, Any]]:
        """
        Extract all timetable cells as structured dicts using pandas for robust cleaning.
        """
        import pandas as pd
        cells = []
        if not self.table:
            return cells

        header_idx = self.structure.get("header_row_index", 0)
        day_col = self.structure.get("day_column_index", 0)
        periods = self.structure.get("periods", [])
        break_cols = set(self.structure.get("break_columns", []) + self.structure.get("lunch_columns", []))

        # Convert to pandas DataFrame for easier cleaning (forward fill merged cells)
        df = pd.DataFrame(self.table)
        
        # We only care about rows after the header
        data_rows = df.iloc[header_idx + 1:].copy()
        
        if data_rows.empty or day_col >= len(df.columns):
            return cells

        # Forward fill the day column to handle vertically merged cells
        data_rows[day_col] = data_rows[day_col].replace('', pd.NA).ffill()

        for _, row in data_rows.iterrows():
            day = str(row.iloc[day_col]).strip() if pd.notna(row.iloc[day_col]) else ""
            if not day or day.lower() == 'nan':
                continue

            col_offset = day_col + 1
            for period_idx, period_header in enumerate(periods):
                col = col_offset + period_idx
                if col >= len(df.columns):
                    break

                if col in break_cols:
                    continue

                raw = str(row.iloc[col]).strip() if pd.notna(row.iloc[col]) else ""
                if not raw or raw == "-" or raw.lower() == 'nan':
                    continue

                parsed = self._parse_cell(raw)
                parsed["day"] = day
                parsed["period"] = period_header
                cells.append(parsed)

        logger.info(f"Extracted {len(cells)} timetable cells using pandas")
        return cells

    def _parse_cell(self, content: str) -> Dict[str, Any]:
        """
        Parse a single timetable cell's raw text content.
        Extracts subject code, room, and class name if present.
        """
        result = {
            "raw_content": content,
            "subject_code": "",
            "room": "",
            "class_name": "",
        }

        lines = [l.strip() for l in content.split("\n") if l.strip()]
        if not lines:
            return result

        # First line is typically the subject code or abbreviation
        result["subject_code"] = lines[0]

        # Look for room patterns like "Room 301", "Lab 2", "R-301"
        room_pattern = re.compile(
            r"(room\s*[-:]?\s*\w+|lab\s*[-:]?\s*\w+|r[-]\d+|hall\s*\w+)",
            re.IGNORECASE,
        )
        for line in lines:
            match = room_pattern.search(line)
            if match:
                result["room"] = match.group(0).strip()
                break

        # Look for class name patterns like "CS4A", "EE2B"
        class_pattern = re.compile(
            r"\b([A-Z]{2,4}\s*\d{1,2}\s*[A-Z]?)\b", re.IGNORECASE
        )
        for line in lines[1:]:
            match = class_pattern.search(line)
            if match:
                result["class_name"] = match.group(0).strip()
                break

        return result
