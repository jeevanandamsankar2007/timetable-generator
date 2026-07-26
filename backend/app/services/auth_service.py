"""
Authentication service.
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse, ChangePasswordRequest
from app.repositories.user_repo import UserRepository
from app.auth.password import hash_password, verify_password
from app.auth.jwt_handler import create_access_token


class AuthService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    def register(self, request: RegisterRequest) -> UserResponse:
        """Register a new user."""
        if self.user_repo.username_exists(request.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )

        hashed = hash_password(request.password)
        user = self.user_repo.create(
            name=request.name,
            username=request.username,
            password_hash=hashed,
        )
        return UserResponse.model_validate(user)

    def login(self, request: LoginRequest) -> TokenResponse:
        """Authenticate user and return JWT."""
        user = self.user_repo.get_by_username(request.username)
        if not user or not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = create_access_token(user_id=user.id, username=user.username)
        return TokenResponse(
            access_token=token,
            user_id=user.id,
            username=user.username,
            name=user.name,
        )

    def change_password(self, user_id: int, request: ChangePasswordRequest) -> dict:
        """Change a user's password."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
            
        if not verify_password(request.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password",
            )
            
        hashed_new_password = hash_password(request.new_password)
        self.user_repo.update_password(user, hashed_new_password)
        
        return {"status": "success", "message": "Password updated successfully"}
