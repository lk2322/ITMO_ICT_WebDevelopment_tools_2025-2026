from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from app.database import get_session
from app import crud, schemas, auth, models
from app.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=schemas.UserRead, status_code=201)
def register(user: schemas.UserCreate, session: Session = Depends(get_session)):
    # Check if user already exists
    db_user = crud.get_user_by_email(session, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    db_user = crud.get_user_by_username(session, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )
    # Create user
    new_user = crud.create_user(session=session, user=user)
    return new_user

@router.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    # Authenticate user
    user = crud.get_user_by_username(session, username=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Create access token
    access_token = auth.create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserRead)
def get_current_user_info(
    current_user: models.User = Depends(get_current_user),
):
    """Get information about the currently authenticated user."""
    return current_user

@router.get("/users", response_model=List[schemas.UserRead])
def get_users(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Get list of all users. Requires authentication."""
    users = crud.get_users(session, skip, limit)
    return users

@router.post("/change-password")
def change_password(
    password_data: schemas.ChangePassword,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Change the current user's password."""
    if not auth.verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password",
        )
    new_hashed_password = auth.get_password_hash(password_data.new_password)
    crud.change_user_password(session, current_user, new_hashed_password)
    return {"message": "Password changed successfully"}
