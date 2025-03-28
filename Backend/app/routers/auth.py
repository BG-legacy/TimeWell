from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Any

from app.core.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.schemas.user import UserCreate, Token, UserResponse
from app.services.user import create_user, authenticate_user

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={401: {"description": "Unauthorized"}},
)

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate) -> Any:
    """
    Create new user.
    """
    new_user = await create_user(user)
    return new_user

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests.
    For OAuth2 compatibility, the email is passed in the username field.
    """
    # OAuth2 form uses username field for the email
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user["email"],
            "user_id": str(user["_id"]),
        },
        expires_delta=access_token_expires,
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    } 