from fastapi import HTTPException
from src.core.config import settings
from src.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from src.core.redis import blacklist_token
from src.core.activity import log_activity
from src.auth import repository
from src.auth.schemas import RegisterRequest, TokenResponse
from src.users.models import User


class AuthService:
    async def register(self, data: RegisterRequest) -> User:
        if await repository.email_exists(data.email):
            raise HTTPException(status_code=400, detail="Email already registered")
        if await repository.username_exists(data.username):
            raise HTTPException(status_code=400, detail="Username already taken")

        user = await repository.create_user(
            data.email, data.username, data.password, data.full_name, data.role,
        )
        await log_activity(user.id, "register", f"Registered as {data.role.value}", "user", user.id)
        return user

    async def verify_email(self, user_id: int) -> User:
        user = await repository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        await repository.activate_user(user)
        await log_activity(user_id, "email_verified", entity_type="user", entity_id=user_id)
        return user

    async def login(self, username: str, password: str) -> TokenResponse:
        user = await repository.get_user_by_username(username)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if settings.EMAIL_VERIFICATION_REQUIRED and not user.is_active:
            raise HTTPException(status_code=403, detail="Email not verified. Please check your inbox.")
        if user.is_blocked:
            raise HTTPException(status_code=403, detail="Account is blocked")

        await log_activity(user.id, "login", entity_type="user", entity_id=user.id)
        token_data = {"sub": str(user.id), "role": user.role.value}
        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await repository.get_user_by_id(int(payload["sub"]))
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        token_data = {"sub": str(user.id), "role": user.role.value}
        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
        )

    async def logout(self, token: str):
        payload = decode_token(token)
        exp = payload.get("exp", 0)
        from datetime import datetime, timezone
        ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 1)
        await blacklist_token(token, ttl)
