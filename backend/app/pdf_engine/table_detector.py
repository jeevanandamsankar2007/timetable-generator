"""
Dynamic table detector - identifies timetable grids vs subject master tables.
All detection is heuristic-based; nothing is hardcoded.
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Common day patterns in various languages and abbreviations
_DAY_PATTERNS = re.compile(
    r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday"
    r"|mon|tue|wed|thu|fri|sat|sun"
    r"|lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\b",
    re.IGNORECASE,
)

# Time period patterns like "08:00-09:00", "I", "II", "Period 1"
_PERIOD_PATTERNS = re.compile(
    r"\b(\d{1,2}[:.]\d{2}\s*(?:am|pm)?\s*[-–\n]?\s*\d{1,2}[:.]\d{2}\s*(?:am|pm)?)\b"
    r"|\b(period\s*\d+|per\s*\d+)\b"
    r"|^(I{1,4}|IV|V|VI|VII|VIII)$",
    re.IGNORECASE,
)

# Break / Lunch patterns
_BREAK_PATTERNS = re.compile(
    r"\b(tea\s*break|break|recess|interval|lunch|noon\s*break)\b",
    re.IGNORECASE,
)


class TableDetector:
    """
    Analyzes extracted table data to classify and detect structure.
    Dynamically identifies days, periods, breaks, and table type.
    """

    @staticmethod
    def classify_tables(
        tables: List[List[List[str]]],
    ) -> Dict[str, Any]:
        """
        Classify extracted tables as timetable grids or subject master tables.

        Args:
            tables: List of 2D arrays from the PDF reader.

        Returns:
            Dict with 'timetable_grids' and 'subject_master_tables' lists.
        """
        timetable_grids = []
        subject_masters = []

        for idx, table in enumerate(tables):
            if not table or len(table) < 2:
                continue

            score = TableDetector._score_as_timetable(table)
            if score >= 3:
                timetable_grids.append({"index": idx, "data": table, "score": score})
                logger.info(f"Table {idx}: classified as TIMETABLE (score={score})")
            else:
                # Check if it looks like a subject master
                if TableDetector._looks_like_subject_master(table):
                    subject_masters.append({"index": idx, "data": table})
                    logger.info(f"Table {idx}: classified as SUBJECT MASTER")
                else:
                    logger.debug(f"Table {idx}: unclassified (score={score})")

        return {
            "timetable_grids": timetable_grids,
            "subject_master_tables": subject_masters,
        }

    @staticmethod
    def _score_as_timetable(table: List[List[str]]) -> int:
        """
        Score a table on how likely it is a timetable grid.
        Higher = more likely a timetable.
        """
        score = 0
        all_text = " ".join(
            cell for row in table for cell in row if cell
        ).lower()

        # Check for day names
        day_matches = _DAY_PATTERNS.findall(all_text)
        if len(day_matches) >= 3:
            score += 3
        elif len(day_matches) >= 1:
            score += 1

        # Check for period/time patterns
        period_matches = _PERIOD_PATTERNS.findall(all_text)
        if len(period_matches) >= 3:
            score += 2
        elif len(period_matches) >= 1:
            score += 1

        # Check for break/lunch
        if _BREAK_PATTERNS.search(all_text):
            score += 1

        # Grid-like structure (many columns, many rows)
        if len(table) >= 4 and len(table[0]) >= 5:
            score += 1

        return score

    @staticmethod
    def _looks_like_subject_master(table: List[List[str]]) -> bool:
        """Check if a table looks like a subject code/name/faculty reference."""
        if not table or len(table) < 2:
            return False

        header = " ".join(cell.lower() for cell in table[0] if cell)
        keywords = ["subject", "code", "faculty", "staff", "name", "course"]
        match_count = sum(1 for kw in keywords if kw in header)
        return match_count >= 2

    @staticmethod
    def detect_structure(
        table: List[List[str]],
    ) -> Dict[str, Any]:
        """
        Dynamically detect the structure of a timetable grid.

        Returns:
            Dict with:
                - days: list of detected day names
                - periods: list of detected period headers
                - break_columns: indices of break/lunch columns
                - day_column_index: which column holds the day names
                - header_row_index: which row holds the period headers
        """
        structure = {
            "days": [],
            "periods": [],
            "break_columns": [],
            "lunch_columns": [],
            "day_column_index": 0,
            "header_row_index": 0,
        }

        if not table or len(table) < 2:
            return structure

        # Detect header row (first row with period/time patterns)
        for row_idx, row in enumerate(table[:5]): # Check up to 5 rows for header
            period_count = sum(
                1 for cell in row
                if cell and _PERIOD_PATTERNS.search(str(cell))
            )
            if period_count >= 2:
                structure["header_row_index"] = row_idx
                break

        if structure["header_row_index"] < len(table):
            header_row = table[structure["header_row_index"]]
        else:
            header_row = []

        # Detect periods and breaks from header
        for col_idx, cell in enumerate(header_row):
            if not cell:
                continue
            cell_lower = cell.strip().lower()

            # Check header cell AND the first data cell in this column for vertical break text
            first_data_cell_lower = ""
            if structure["header_row_index"] + 1 < len(table):
                row_below = table[structure["header_row_index"] + 1]
                if col_idx < len(row_below):
                    first_data_cell_lower = (row_below[col_idx] or "").strip().lower().replace('\n', '').replace(' ', '')

            # For vertical text, strip newlines and spaces to match 'teabreak' or 'lunchbreak'
            cell_lower_clean = cell_lower.replace('\n', '').replace(' ', '')
            
            is_break = bool(re.search(r'(teabreak|break|recess|interval|lunch|noonbreak)', cell_lower_clean)) or \
                       bool(re.search(r'(teabreak|break|recess|interval|lunch|noonbreak)', first_data_cell_lower))

            if is_break:
                if "lunch" in cell_lower_clean or "noon" in cell_lower_clean or "lunch" in first_data_cell_lower or "noon" in first_data_cell_lower:
                    structure["lunch_columns"].append(col_idx)
                else:
                    structure["break_columns"].append(col_idx)
                structure["periods"].append(cell.strip())
            elif col_idx > 0 or _PERIOD_PATTERNS.search(cell_lower):
                structure["periods"].append(cell.strip())

        # Detect day column and day names from data rows
        for col_idx in range(min(2, len(table[0]))):
            day_count = 0
            days = []
            for row_idx in range(structure["header_row_index"] + 1, len(table)):
                cell = table[row_idx][col_idx] if col_idx < len(table[row_idx]) else ""
                if cell and _DAY_PATTERNS.search(cell.lower()):
                    day_count += 1
                    days.append(cell.strip())
            if day_count >= 2:
                structure["day_column_index"] = col_idx
                structure["days"] = days
                break

        logger.info(
            f"Detected structure: {len(structure['days'])} days, "
            f"{len(structure['periods'])} periods, "
            f"{len(structure['break_columns'])} breaks, "
            f"{len(structure['lunch_columns'])} lunch cols"
        )
        return structure
