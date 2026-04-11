from fastapi import HTTPException
from src.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from src.core.redis import blacklist_token
from src.users.models import User, CompanyProfile, StudentProfile, RoleEnum
from src.auth.schemas import RegisterRequest, TokenResponse
from src.core.activity import log_activity
from tortoise.transactions import in_transaction


class AuthService:
    async def register(self, data: RegisterRequest) -> User:
        if await User.filter(email=data.email).exists():
            raise HTTPException(status_code=400, detail="Email already registered")
        if await User.filter(username=data.username).exists():
            raise HTTPException(status_code=400, detail="Username already taken")

        async with in_transaction():
            user = await User.create(
                email=data.email, username=data.username,
                hashed_password=hash_password(data.password),
                full_name=data.full_name, role=data.role,
                is_active=False,
            )

            if data.role == RoleEnum.company:
                await CompanyProfile.create(user=user, company_name=data.username)
            elif data.role == RoleEnum.student:
                await StudentProfile.create(user=user)

        await user.fetch_related("skills")
        await log_activity(user.id, "register", f"Registered as {data.role.value}", "user", user.id)
        return user

    async def verify_email(self, user_id: int) -> User:
        user = await User.filter(id=user_id).prefetch_related("skills").first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.is_active = True
        await user.save()
        await log_activity(user_id, "email_verified", entity_type="user", entity_id=user_id)
        return user

    async def login(self, username: str, password: str) -> TokenResponse:
        user = await User.filter(username=username).first()
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not user.is_active:
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
        user = await User.filter(id=int(payload["sub"])).first()
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
