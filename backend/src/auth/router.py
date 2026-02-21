from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.postgres import get_db
from src.core.dependencies import get_current_user, oauth2_scheme
from src.core.email import send_welcome_email
from src.users.models import User
from src.users.schemas import UserResponse
from src.auth.schemas import RegisterRequest, LoginRequest, TokenResponse, RefreshTokenRequest
from src.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: RegisterRequest, bg: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user = await service.register(data)
    bg.add_task(send_welcome_email, user.email, user.username)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService(db).login(data.username, data.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService(db).refresh(data.refresh_token)


@router.post("/logout", status_code=204)
async def logout(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    await AuthService(db).logout(token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
