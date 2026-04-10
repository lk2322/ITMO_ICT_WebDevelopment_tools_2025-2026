from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.database import get_session
from app import crud, schemas, models
from app.dependencies import get_current_user

router = APIRouter(prefix="/tags", tags=["tags"])

@router.post("/", response_model=schemas.TagRead, status_code=201)
def create_tag(
    tag: schemas.TagCreate,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Create a new tag for the current user."""
    existing = crud.get_tag_by_name_and_user(session, tag.name, current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag with this name already exists",
        )
    db_tag = crud.create_tag(session, tag, current_user.id)
    return db_tag

@router.get("/", response_model=List[schemas.TagRead])
def read_tags(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Get all tags for the current user."""
    tags = crud.get_tags_for_user(session, current_user.id, skip, limit)
    return tags

@router.get("/{tag_id}", response_model=schemas.TagRead)
def read_tag(
    tag_id: int,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Get a specific tag by ID (must belong to current user)."""
    db_tag = crud.get_tag_by_id(session, tag_id)
    if not db_tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    if db_tag.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return db_tag

@router.patch("/{tag_id}", response_model=schemas.TagRead)
def update_tag(
    tag_id: int,
    tag_update: schemas.TagUpdate,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Update a tag."""
    db_tag = crud.get_tag_by_id(session, tag_id)
    if not db_tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    if db_tag.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    updated_tag = crud.update_tag(session, db_tag, tag_update.model_dump(exclude_unset=True))
    return updated_tag

@router.delete("/{tag_id}")
def delete_tag(
    tag_id: int,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Delete a tag."""
    db_tag = crud.get_tag_by_id(session, tag_id)
    if not db_tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    if db_tag.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    crud.delete_tag(session, db_tag)
    return {"message": "Tag deleted successfully"}