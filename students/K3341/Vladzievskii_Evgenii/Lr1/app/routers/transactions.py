from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.database import get_session
from app import crud, schemas, models
from app.dependencies import get_current_user

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.post("/", response_model=schemas.TransactionRead, status_code=201)
def create_transaction(
    transaction: schemas.TransactionCreate,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Create a new transaction for the current user."""
    # Verify category belongs to user
    category = crud.get_category_by_id(session, transaction.category_id)
    if not category or category.user_id != current_user.id:
        raise HTTPException(status_code=400, detail="Invalid category")
    # Verify tags belong to user
    if transaction.tag_ids:
        for tag_id in transaction.tag_ids:
            tag = crud.get_tag_by_id(session, tag_id)
            if not tag or tag.user_id != current_user.id:
                raise HTTPException(status_code=400, detail=f"Invalid tag id {tag_id}")
    db_transaction = crud.create_transaction(session, transaction, current_user.id)
    return db_transaction

@router.get("/", response_model=List[schemas.TransactionRead])
def read_transactions(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Get all transactions for the current user."""
    transactions = crud.get_transactions_for_user(session, current_user.id, skip, limit)
    return transactions

@router.get("/{transaction_id}", response_model=schemas.TransactionRead)
def read_transaction(
    transaction_id: int,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Get a specific transaction by ID (must belong to current user)."""
    db_transaction = crud.get_transaction_by_id(session, transaction_id)
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if db_transaction.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return db_transaction

@router.patch("/{transaction_id}", response_model=schemas.TransactionRead)
def update_transaction(
    transaction_id: int,
    transaction_update: schemas.TransactionUpdate,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Update a transaction."""
    db_transaction = crud.get_transaction_by_id(session, transaction_id)
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if db_transaction.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    # Validate category if provided
    if transaction_update.category_id is not None:
        category = crud.get_category_by_id(session, transaction_update.category_id)
        if not category or category.user_id != current_user.id:
            raise HTTPException(status_code=400, detail="Invalid category")
    # Validate tags if provided
    if transaction_update.tag_ids is not None:
        for tag_id in transaction_update.tag_ids:
            tag = crud.get_tag_by_id(session, tag_id)
            if not tag or tag.user_id != current_user.id:
                raise HTTPException(status_code=400, detail=f"Invalid tag id {tag_id}")
    updated_transaction = crud.update_transaction(
        session, db_transaction, transaction_update.model_dump(exclude_unset=True)
    )
    return updated_transaction

@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Delete a transaction."""
    db_transaction = crud.get_transaction_by_id(session, transaction_id)
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if db_transaction.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    crud.delete_transaction(session, db_transaction)
    return {"message": "Transaction deleted successfully"}