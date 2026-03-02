from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger

from src.auth.dependencies import get_current_user
from src.auth.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from src.auth.service import (
    blacklist_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from src.users.models import CompanyProfile, StudentProfile, User, UserRole

router = APIRouter()
bearer_scheme = HTTPBearer()


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest):
    if body.role == UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Cannot register as admin")

    existing = await User.get_or_none(email=body.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = await User.create(
        email=body.email,
        hashed_password=hash_password(body.password),
        role=body.role,
    )

    if body.role == UserRole.STUDENT:
        await StudentProfile.create(user=user)
    elif body.role == UserRole.COMPANY:
        await CompanyProfile.create(user=user)

    logger.info("User registered: {} ({})", user.email, user.role.value)

    return TokenResponse(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    user = await User.get_or_none(email=body.email)
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    logger.info("User logged in: {}", user.email)

    return TokenResponse(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest):
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = await User.get_or_none(id=payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")

    blacklist_token(body.refresh_token)

    return TokenResponse(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/logout", status_code=204)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    _: User = Depends(get_current_user),
):
    blacklist_token(credentials.credentials)
    logger.info("User logged out")
