"""
Faculty model - stores unique faculty members with normalized names.
"""
from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from app.database.base import Base

class Faculty(Base):
    """Individual faculty member, deduplicated via NormalizedName."""

    __tablename__ = "faculty"

    id = Column(Integer, primary_key=True, autoincrement=True)
    upload_id = Column(Integer, ForeignKey("uploaded_pdfs.id", ondelete="CASCADE"), nullable=False, index=True)
    faculty_name = Column(String(255), nullable=False)
    normalized_name = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('upload_id', 'normalized_name', name='uix_upload_normalized_name'),
    )

    # Relationships
    upload = relationship("UploadedPDF", backref=backref("faculty", cascade="all, delete-orphan"))
    mappings = relationship("FacultyMapping", back_populates="faculty", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Faculty(id={self.id}, name='{self.faculty_name}', upload={self.upload_id})>"
