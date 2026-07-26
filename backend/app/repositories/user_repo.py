"""
User repository - data access layer for User model.
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """Handles all database operations for the User model."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Find a user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_username(self, username: str) -> Optional[User]:
        """Find a user by username."""
        return self.db.query(User).filter(User.username == username).first()

    def create(self, name: str, username: str, password_hash: str) -> User:
        """Create a new user."""
        user = User(name=name, username=username, password_hash=password_hash)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def username_exists(self, username: str) -> bool:
        """Check if a username is already taken."""
        return self.db.query(User).filter(User.username == username).count() > 0

    def update_password(self, user: User, new_password_hash: str) -> User:
        """Update a user's password."""
        user.password_hash = new_password_hash
        self.db.commit()
        self.db.refresh(user)
        return user
