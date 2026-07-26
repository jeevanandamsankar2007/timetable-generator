"""
Faculty name normalizer for deduplication and matching.
"""
import re
from typing import Optional


# Prefixes to strip during normalization
_PREFIXES = re.compile(
    r"^(dr\.?|prof\.?|mr\.?|mrs\.?|ms\.?|shri\.?|smt\.?)\s+",
    re.IGNORECASE,
)


def normalize_faculty_name(name: str) -> str:
    """
    Normalize a faculty name for deduplication.

    Steps:
        1. Trim whitespace
        2. Lowercase
        3. Remove honorific prefixes (Dr., Prof., Mr., Mrs., etc.)
        4. Collapse multiple spaces
        5. Strip trailing/leading whitespace

    Args:
        name: Raw faculty name string.

    Returns:
        Normalized lowercase string suitable for unique comparison.
    """
    if not name:
        return ""

    result = name.strip().lower()
    # Replace dots and commas with spaces to handle cases like "Dr.P.Name"
    result = result.replace(".", " ").replace(",", " ")
    # Remove honorific prefixes
    result = _PREFIXES.sub("", result)
    # Collapse multiple spaces
    result = re.sub(r"\s+", " ", result).strip()
    return result


def clean_display_name(name: str) -> str:
    """
    Clean a faculty name for display (preserves casing and prefixes).
    Only trims whitespace and collapses double spaces.
    """
    if not name:
        return ""
    return re.sub(r"\s+", " ", name.strip())
