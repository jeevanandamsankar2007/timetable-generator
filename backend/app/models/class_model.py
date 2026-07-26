"""
Class model - stores class information (department, semester, name).
"""
from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from app.database.base import Base


class Class(Base):
    """Academic class (e.g., CS4A, EE2B)."""

    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    upload_id = Column(Integer, ForeignKey("uploaded_pdfs.id", ondelete="CASCADE"), nullable=False, index=True)
    department = Column(String(100), nullable=False)
    semester = Column(String(20), nullable=False)
    class_name = Column(String(50), nullable=False)
    academic_year = Column(String(20), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('upload_id', 'class_name', name='uix_upload_class_name'),
    )

    # Relationships
    upload = relationship("UploadedPDF", backref=backref("classes", cascade="all, delete-orphan"))

    def __repr__(self) -> str:
        return f"<Class(id={self.id}, name='{self.class_name}', upload={self.upload_id})>"
