"""
Validation engine - checks preview data for conflicts, missing data, etc.
"""
from typing import List, Dict, Any
from app.models.preview_data import PreviewData


class DataValidator:
    """
    Validates extracted timetable data before it can be approved.
    Detects missing fields, conflicts, etc.
    """

    @staticmethod
    def validate_preview_items(items: List[PreviewData]) -> None:
        """
        Run validation rules on a list of preview items.
        Updates validation_status and validation_message on each item in-memory.
        """
        # Group by faculty, day, and period to detect conflicts
        faculty_schedule = {}

        for item in items:
            # Skip already errored items
            if item.validation_status == "error":
                continue

            status = "valid"
            messages = []

            # Rule 1: Missing essential data
            if not item.subject_code:
                status = "error"
                messages.append("Missing subject code")

            if not item.faculty_name:
                status = "error"
                messages.append("Missing faculty name")

            # Rule 2: Conflict detection (same faculty, same day, same period)
            if item.faculty_name and item.day and item.period:
                key = (item.faculty_name, item.day, item.period)
                if key in faculty_schedule:
                    existing_item = faculty_schedule[key]
                    if item.class_name == existing_item.class_name:
                        # Duplicate Entry (Ignore) - Keep it valid, DB will deduplicate
                        pass
                    else:
                        # Scheduling Conflict (Show Warning)
                        status = "warning"
                        messages.append(
                            f"Conflict: Faculty already booked for {existing_item.subject_code} in {existing_item.class_name}"
                        )
                        # Also mark the existing one as warning
                        existing_item.validation_status = "warning"
                        existing_item.validation_message = (
                            f"Conflict: Double-booked with {item.subject_code} in {item.class_name}"
                        )
                else:
                    faculty_schedule[key] = item

            if status != "valid" or item.validation_status == "valid": 
                item.validation_status = status
            if messages:
                item.validation_message = "; ".join(messages)
