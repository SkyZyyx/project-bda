# ==============================================================================
# AUTHENTICATION ROUTER
# ==============================================================================
# Handles user login, token generation, and user management.
# We use JWT (JSON Web Tokens) for stateless authentication.
# ==============================================================================

from datetime import datetime, timezone, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    require_role
)
from app.models import User
from app.schemas import Token, UserLogin, UserCreate, UserResponse

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate a user and return a JWT access token.
    
    This endpoint accepts username (email) and password via OAuth2 password flow.
    If credentials are valid, it returns a JWT token that can be used to
    authenticate subsequent requests.
    
    The token should be included in the Authorization header:
    `Authorization: Bearer <token>`
    """
    # Find the user by email
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    # Check if user exists and password is correct
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Update last login timestamp
    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    
    # Create JWT token with user information
    # "sub" (subject) is a standard JWT claim for the user identifier
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role
        }
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role(["admin"]))
):
    """
    Register a new user (admin only).
    
    Only administrators can create new user accounts.
    This prevents unauthorized user registration.
    
    The password will be securely hashed using bcrypt before storage.
    """
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user with hashed password
    new_user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role,
        professor_id=user_data.professor_id,
        student_id=user_data.student_id,
        department_id=user_data.department_id
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get the current authenticated user's information.
    
    This endpoint returns the full user profile based on the JWT token
    provided in the Authorization header.
    """
    result = await db.execute(
        select(User).where(User.id == UUID(current_user["id"]))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Change the current user's password.
    
    Requires the old password for verification before setting the new one.
    The new password must be at least 8 characters.
    """
    # Get the user from database
    result = await db.execute(
        select(User).where(User.id == UUID(current_user["id"]))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify old password
    if not verify_password(old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    # Validate new password
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
        )
    
    # Update password
    user.password_hash = get_password_hash(new_password)
    await db.commit()
    
    return {"message": "Password changed successfully"}
