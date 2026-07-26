"""
ValidationLog model - persists validation errors for auditing and debugging.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database.base import Base


class ValidationLog(Base):
    """
    Persists validation messages (warnings and errors) for a specific upload.
    This helps in tracking parsing accuracy and debugging failures.
    """

    __tablename__ = "validation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    upload_id = Column(
        Integer, ForeignKey("uploaded_pdfs.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    status = Column(String(50), nullable=False) # 'warning' or 'error'
    message = Column(Text, nullable=False)
    cell_reference = Column(String(100), nullable=True) # e.g., 'Day: Monday, Period: 1'
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    upload = relationship("UploadedPDF")

    def __repr__(self) -> str:
        return f"<ValidationLog(id={self.id}, status='{self.status}')>"
