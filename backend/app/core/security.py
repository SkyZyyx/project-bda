# ==============================================================================
# AUTHENTICATION AND SECURITY MODULE
# ==============================================================================
# This module handles password hashing, JWT token creation, and user authentication.
# We use industry-standard libraries: passlib for passwords, python-jose for JWTs.
# ==============================================================================

from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import get_db

settings = get_settings()

# Password hashing context
# bcrypt is one of the most secure hashing algorithms available
# It automatically handles salting (adding random data to passwords)
pwd_context = CryptContext(
    schemes=["bcrypt"],  # Use bcrypt algorithm
    deprecated="auto"     # Automatically handle algorithm upgrades
)

# OAuth2 password bearer scheme
# This tells FastAPI where to look for the JWT token (Authorization header)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_prefix}/auth/login"
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    This function uses bcrypt's constant-time comparison to prevent
    timing attacks (where attackers measure response time to guess passwords).
    
    Args:
        plain_password: The password entered by the user
        hashed_password: The hash stored in the database
        
    Returns:
        bool: True if passwords match, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password for secure storage.
    
    bcrypt automatically:
    - Generates a random salt
    - Uses a work factor (cost) that makes brute-force attacks slow
    - Produces a hash that includes the salt (for verification later)
    
    Args:
        password: Plain text password to hash
        
    Returns:
        str: The hashed password (safe to store in database)
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT (JSON Web Token) for authentication.
    
    JWTs are self-contained tokens that encode user information.
    They're signed with our secret key, so we can verify they weren't tampered with.
    
    Structure of a JWT:
    - Header: Algorithm and token type
    - Payload: User data + expiration time
    - Signature: Cryptographic signature
    
    Args:
        data: Dictionary of claims to encode (usually user ID, email, role)
        expires_delta: Optional custom expiration time
        
    Returns:
        str: Encoded JWT token
    """
    # Create a copy so we don't modify the original data
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    # Add expiration claim (standard JWT claim)
    to_encode.update({"exp": expire})
    
    # Create and return the token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT token.
    
    This function:
    1. Verifies the signature (token wasn't modified)
    2. Checks expiration time
    3. Returns the payload if valid
    
    Args:
        token: The JWT token string
        
    Returns:
        dict or None: Token payload if valid, None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        # Token is invalid (expired, wrong signature, etc.)
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    FastAPI dependency that extracts and validates the current user from JWT.
    
    This is used to protect routes - just add it as a dependency:
        @app.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"user": user}
    
    Args:
        token: JWT from Authorization header (injected by FastAPI)
        db: Database session (injected by FastAPI)
        
    Returns:
        dict: User information from token
        
    Raises:
        HTTPException: 401 if token is invalid
    """
    # Standard exception for authentication failures
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decode the token
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    # Extract user information
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # Return user info (in a real app, you might fetch fresh data from DB here)
    return {
        "id": user_id,
        "email": payload.get("email"),
        "role": payload.get("role"),
    }


def require_role(allowed_roles: list[str]):
    """
    Factory function to create role-checking dependencies.
    
    Usage:
        @app.get("/admin-only")
        async def admin_route(
            user: dict = Depends(require_role(["admin", "dean"]))
        ):
            return {"message": "Welcome, admin!"}
    
    Args:
        allowed_roles: List of role names that can access the route
        
    Returns:
        Dependency function that checks user role
    """
    async def check_role(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return user
    
    return check_role
