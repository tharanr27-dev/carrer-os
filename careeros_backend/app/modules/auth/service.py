from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.modules.auth.models import User, UserStatus
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import Token, UserCreate, UserLogin


class AuthService:
    def __init__(self, session: AsyncSession):
        self.repository = AuthRepository(session)

    async def authenticate(self, credentials: UserLogin) -> Token:
        user = await self.repository.get_user_by_email(credentials.email)
        if not user or not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)

        return Token(access_token=access_token, refresh_token=refresh_token)

    async def register(self, user_in: UserCreate) -> User:
        existing_user = await self.repository.get_user_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
            )

        hashed_pw = get_password_hash(user_in.password)
        # Set status to ACTIVE immediately so the user can log in right away.
        # Email verification flow can be layered on top later.
        new_user = User(
            email=user_in.email,
            hashed_password=hashed_pw,
            status=UserStatus.ACTIVE,
        )
        return await self.repository.create_user(new_user)
