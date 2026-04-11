import secrets
from fastapi import APIRouter, Depends, BackgroundTasks, Request, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from src.core.dependencies import get_current_user, oauth2_scheme
from src.core.email import send_verification_email, send_welcome_email
from src.core.redis import rate_limit_check, cache_set, cache_get, cache_delete
from src.users.models import User
from src.users.schemas import UserResponse
from src.auth.schemas import RegisterRequest, LoginRequest, TokenResponse, RefreshTokenRequest
from src.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: RegisterRequest, bg: BackgroundTasks):
    service = AuthService()
    user = await service.register(data)

    verify_token = secrets.token_urlsafe(32)
    await cache_set(f"email_verify:{verify_token}", str(user.id), ttl=86400)

    bg.add_task(send_verification_email, user.email, user.username, verify_token)
    return user


@router.get("/verify-email")
async def verify_email(token: str, bg: BackgroundTasks):
    user_id = await cache_get(f"email_verify:{token}")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    service = AuthService()
    user = await service.verify_email(int(user_id))
    await cache_delete(f"email_verify:{token}")

    bg.add_task(send_welcome_email, user.email, user.username)
    return {"message": "Email verified successfully"}


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    client_ip = request.client.host if request.client else "unknown"
    if not await rate_limit_check(f"login:{client_ip}", max_requests=5, window=60):
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again in 1 minute.")
    return await AuthService().login(form_data.username, form_data.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshTokenRequest):
    return await AuthService().refresh(data.refresh_token)


@router.post("/logout", status_code=204)
async def logout(token: str = Depends(oauth2_scheme)):
    await AuthService().logout(token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
