"""
Preview repository - data access layer for PreviewData staging table.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.preview_data import PreviewData


class PreviewRepository:
    """Handles all database operations for the PreviewData staging table."""

    def __init__(self, db: Session):
        self.db = db

    def bulk_insert(self, items: List[dict]) -> int:
        """
        Batch insert preview rows for a given upload.
        Returns the number of rows inserted.
        """
        objects = [PreviewData(**item) for item in items]
        self.db.add_all(objects)
        self.db.flush()
        return len(objects)

    def get_by_upload(self, upload_id: int) -> List[PreviewData]:
        """Get all preview items for an upload."""
        return (
            self.db.query(PreviewData)
            .filter(PreviewData.upload_id == upload_id)
            .order_by(PreviewData.day, PreviewData.period)
            .all()
        )

    def get_by_id(self, item_id: int) -> Optional[PreviewData]:
        """Get a single preview row."""
        return self.db.query(PreviewData).filter(PreviewData.id == item_id).first()

    def approve_all(self, upload_id: int) -> int:
        """Mark all preview items for an upload as approved."""
        count = (
            self.db.query(PreviewData)
            .filter(PreviewData.upload_id == upload_id)
            .update({"is_approved": 1})
        )
        self.db.flush()
        return count

    def reject_all(self, upload_id: int) -> int:
        """Mark all preview items for an upload as rejected."""
        count = (
            self.db.query(PreviewData)
            .filter(PreviewData.upload_id == upload_id)
            .update({"is_approved": -1})
        )
        self.db.flush()
        return count

    def approve_selected(self, item_ids: List[int]) -> int:
        """Approve specific preview items by ID."""
        count = (
            self.db.query(PreviewData)
            .filter(PreviewData.id.in_(item_ids))
            .update({"is_approved": 1}, synchronize_session="fetch")
        )
        self.db.flush()
        return count

    def update_item(self, item_id: int, updates: dict) -> Optional[PreviewData]:
        """Update a single preview row (for editing)."""
        item = self.get_by_id(item_id)
        if not item:
            return None
        for key, value in updates.items():
            if hasattr(item, key) and value is not None:
                setattr(item, key, value)
        self.db.flush()
        self.db.refresh(item)
        return item

    def delete_item(self, item_id: int) -> bool:
        """Delete a single preview row."""
        item = self.get_by_id(item_id)
        if not item:
            return False
        self.db.delete(item)
        self.db.flush()
        return True

    def get_approved(self, upload_id: int) -> List[PreviewData]:
        """Get all approved preview items for an upload."""
        return (
            self.db.query(PreviewData)
            .filter(
                PreviewData.upload_id == upload_id,
                PreviewData.is_approved == 1,
            )
            .all()
        )

    def delete_by_upload(self, upload_id: int) -> int:
        """Delete all preview data for an upload (cleanup after commit)."""
        count = (
            self.db.query(PreviewData)
            .filter(PreviewData.upload_id == upload_id)
            .delete()
        )
        self.db.flush()
        return count

    def count_by_status(self, upload_id: int) -> dict:
        """Count preview items grouped by validation status."""
        results = (
            self.db.query(
                PreviewData.validation_status,
                func.count(PreviewData.id),
            )
            .filter(PreviewData.upload_id == upload_id)
            .group_by(PreviewData.validation_status)
            .all()
        )
        return {status: count for status, count in results}
