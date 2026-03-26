from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib
import base64
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from src.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    # Bcrypt has a 72-byte limit, so hash password first with SHA-256 to handle any length
    # This prevents "password cannot be longer than 72 bytes" error
    sha256_hash = hashlib.sha256(password.encode('utf-8')).digest()
    # Encode to base64 so it's safe as a string (always < 72 bytes)
    password_to_hash = base64.b64encode(sha256_hash).decode('utf-8')
    return pwd_context.hash(password_to_hash)


def verify_password(plain: str, hashed: str) -> bool:
    # Apply the same SHA-256 hashing for verification
    sha256_hash = hashlib.sha256(plain.encode('utf-8')).digest()
    password_to_verify = base64.b64encode(sha256_hash).decode('utf-8')
    return pwd_context.verify(password_to_verify, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
