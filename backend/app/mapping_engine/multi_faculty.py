"""
Multi-faculty handler for laboratory sessions.

When a single timetable cell has multiple assigned faculty (e.g. a lab
session), this module splits the single mapped entry into individual
faculty mapping records.
"""
import logging
from typing import List, Dict, Any

from app.mapping_engine.normalizer import normalize_faculty_name

logger = logging.getLogger(__name__)


def expand_multi_faculty(
    mapped_cells: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Expand cells with multiple faculty into individual preview rows.

    A lab cell like:
        subject_code=EP, faculty_names=["Dr A", "Dr B", "Dr C"]
    becomes three separate preview rows, each with one faculty name
    but sharing the same day, period, subject, and room.

    Args:
        mapped_cells: Output from TimetableMapper.map_cells().

    Returns:
        Expanded list where each row has exactly one faculty_name.
    """
    expanded = []
    for cell in mapped_cells:
        faculty_names = cell.get("faculty_names", [])

        if not faculty_names:
            # No faculty assigned - keep as-is
            row = {**cell}
            row["faculty_name"] = ""
            row["normalized_faculty_name"] = ""
            expanded.append(row)
        elif len(faculty_names) == 1:
            row = {**cell}
            row["faculty_name"] = faculty_names[0]
            row["normalized_faculty_name"] = normalize_faculty_name(
                faculty_names[0]
            )
            expanded.append(row)
        else:
            # Multiple faculty → expand to N rows
            for fname in faculty_names:
                row = {**cell}
                row["faculty_name"] = fname
                row["normalized_faculty_name"] = normalize_faculty_name(fname)
                expanded.append(row)

            logger.debug(
                f"Expanded multi-faculty cell: {cell.get('subject_code')} → "
                f"{len(faculty_names)} faculty"
            )

    multi_count = sum(
        1 for c in mapped_cells
        if len(c.get("faculty_names", [])) > 1
    )
    logger.info(
        f"Expanded {multi_count} multi-faculty cells → "
        f"{len(expanded)} total preview rows"
    )
    return expanded
