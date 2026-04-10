from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.database import get_session
from app import crud, schemas, models
from app.dependencies import get_current_user

router = APIRouter(prefix="/categories", tags=["categories"])

@router.post("/", response_model=schemas.CategoryRead, status_code=201)
def create_category(
    category: schemas.CategoryCreate,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Create a new category for the current user."""
    db_category = crud.create_category(session, category, current_user.id)
    return db_category

@router.get("/", response_model=List[schemas.CategoryRead])
def read_categories(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Get all categories for the current user."""
    categories = crud.get_categories_for_user(session, current_user.id, skip, limit)
    return categories

@router.get("/{category_id}", response_model=schemas.CategoryRead)
def read_category(
    category_id: int,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Get a specific category by ID (must belong to current user)."""
    db_category = crud.get_category_by_id(session, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    if db_category.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return db_category

@router.patch("/{category_id}", response_model=schemas.CategoryRead)
def update_category(
    category_id: int,
    category_update: schemas.CategoryUpdate,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Update a category."""
    db_category = crud.get_category_by_id(session, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    if db_category.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    updated_category = crud.update_category(session, db_category, category_update.model_dump(exclude_unset=True))
    return updated_category

@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Delete a category."""
    db_category = crud.get_category_by_id(session, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    if db_category.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    crud.delete_category(session, db_category)
    return {"message": "Category deleted successfully"}