from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.database import get_session
from app import crud, schemas, models
from app.dependencies import get_current_user

router = APIRouter(prefix="/budgets", tags=["budgets"])

@router.post("/", response_model=schemas.BudgetRead, status_code=201)
def create_budget(
    budget: schemas.BudgetCreate,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Create a new budget for the current user."""
    # If category_id provided, verify category belongs to user
    if budget.category_id is not None:
        category = crud.get_category_by_id(session, budget.category_id)
        if not category or category.user_id != current_user.id:
            raise HTTPException(status_code=400, detail="Invalid category")
    db_budget = crud.create_budget(session, budget, current_user.id)
    return db_budget

@router.get("/", response_model=List[schemas.BudgetRead])
def read_budgets(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Get all budgets for the current user."""
    budgets = crud.get_budgets_for_user(session, current_user.id, skip, limit)
    return budgets

@router.get("/{budget_id}", response_model=schemas.BudgetRead)
def read_budget(
    budget_id: int,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Get a specific budget by ID (must belong to current user)."""
    db_budget = crud.get_budget_by_id(session, budget_id)
    if not db_budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    if db_budget.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return db_budget

@router.patch("/{budget_id}", response_model=schemas.BudgetRead)
def update_budget(
    budget_id: int,
    budget_update: schemas.BudgetUpdate,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Update a budget."""
    db_budget = crud.get_budget_by_id(session, budget_id)
    if not db_budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    if db_budget.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    # Validate category if provided
    if budget_update.category_id is not None:
        category = crud.get_category_by_id(session, budget_update.category_id)
        if not category or category.user_id != current_user.id:
            raise HTTPException(status_code=400, detail="Invalid category")
    updated_budget = crud.update_budget(
        session, db_budget, budget_update.model_dump(exclude_unset=True)
    )
    return updated_budget

@router.delete("/{budget_id}")
def delete_budget(
    budget_id: int,
    session: Session = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """Delete a budget."""
    db_budget = crud.get_budget_by_id(session, budget_id)
    if not db_budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    if db_budget.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    crud.delete_budget(session, db_budget)
    return {"message": "Budget deleted successfully"}