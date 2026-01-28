"""
Authentication and authorization for API.
"""

import secrets
import hashlib
from typing import Optional
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.database import get_db


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# API key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# JWT Bearer
security = HTTPBearer(auto_error=False)

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Validate API key from header.
    
    Usage:
        @router.get("/protected")
        async def protected_route(api_key: str = Depends(get_api_key)):
            ...
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # TODO: Verify against database
    # For now, check against config (development only)
    valid_keys = getattr(settings, "api_keys", [])
    
    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    
    return api_key


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> dict:
    """
    Get current user from JWT token.
    
    Usage:
        @router.get("/me")
        async def get_me(user: dict = Depends(get_current_user)):
            ...
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


class OptionalAuth:
    """
    Optional authentication - allows both authenticated and unauthenticated access.
    
    Usage:
        @router.get("/")
        async def home(user: Optional[dict] = Depends(OptionalAuth())):
            if user:
                # Authenticated
            else:
                # Anonymous
    """
    
    async def __call__(
        self,
        credentials: HTTPAuthorizationCredentials = Security(security),
    ) -> Optional[dict]:
        if not credentials:
            return None
        
        try:
            payload = verify_token(credentials.credentials)
            return payload
        except:
            return None


# Rate limiting (simple in-memory implementation)
class RateLimiter:
    """
    Simple in-memory rate limiter.
    
    Usage:
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        
        @router.get("/")
        async def route(api_key: str = Depends(get_api_key)):
            limiter.check(api_key)
            ...
    """
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # key -> [(timestamp, count)]
    
    def check(self, key: str):
        """Check if request is allowed. Raises HTTPException if rate limit exceeded."""
        now = datetime.utcnow()
        
        # Clean old requests
        if key in self.requests:
            self.requests[key] = [
                (ts, count) for ts, count in self.requests[key]
                if (now - ts).total_seconds() < self.window_seconds
            ]
        
        # Count requests in window
        if key not in self.requests:
            self.requests[key] = []
        
        request_count = sum(count for _, count in self.requests[key])
        
        if request_count >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds}s.",
            )
        
        # Add this request
        self.requests[key].append((now, 1))
    
    def reset(self, key: str):
        """Reset rate limit for a key."""
        if key in self.requests:
            del self.requests[key]


# Global rate limiter instance
global_rate_limiter = RateLimiter(
    max_requests=settings.rate_limit_per_minute,
    window_seconds=60,
)
