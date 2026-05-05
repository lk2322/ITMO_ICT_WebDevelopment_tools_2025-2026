from sqlmodel import Session, select
from typing import Optional
from app.models import User, Category, Transaction, Budget, Tag, TransactionTagLink
from app.schemas import UserCreate, CategoryCreate, TransactionCreate, BudgetCreate, TagCreate
from app.auth import get_password_hash

# User CRUD
def get_user_by_email(session: Session, email: str) -> Optional[User]:
    return session.exec(select(User).where(User.email == email)).first()

def get_user_by_username(session: Session, username: str) -> Optional[User]:
    return session.exec(select(User).where(User.username == username)).first()

def create_user(session: Session, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

def get_users(session: Session, skip: int = 0, limit: int = 100):
    return session.exec(select(User).offset(skip).limit(limit)).all()

def get_user_by_id(session: Session, user_id: int) -> Optional[User]:
    return session.get(User, user_id)

def change_user_password(session: Session, user: User, new_hashed_password: str) -> User:
    user.hashed_password = new_hashed_password
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

# Category CRUD
def create_category(session: Session, category: CategoryCreate, user_id: int) -> Category:
    db_category = Category(**category.model_dump(), user_id=user_id)
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category

def get_categories_for_user(session: Session, user_id: int, skip: int = 0, limit: int = 100):
    statement = select(Category).where(Category.user_id == user_id).offset(skip).limit(limit)
    return session.exec(statement).all()

def get_category_by_id(session: Session, category_id: int) -> Optional[Category]:
    return session.get(Category, category_id)

def update_category(session: Session, db_category: Category, category_update: dict) -> Category:
    for key, value in category_update.items():
        setattr(db_category, key, value)
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category

def delete_category(session: Session, db_category: Category) -> None:
    session.delete(db_category)
    session.commit()

# Transaction CRUD
def create_transaction(session: Session, transaction: TransactionCreate, user_id: int) -> Transaction:
    db_transaction = Transaction(**transaction.model_dump(exclude={"tag_ids"}), user_id=user_id)
    session.add(db_transaction)
    session.commit()
    session.refresh(db_transaction)
    if transaction.tag_ids:
        for tag_id in transaction.tag_ids:
            link = TransactionTagLink(transaction_id=db_transaction.id, tag_id=tag_id)
            session.add(link)
        session.commit()
        session.refresh(db_transaction)
    return db_transaction

def get_transactions_for_user(session: Session, user_id: int, skip: int = 0, limit: int = 100):
    statement = select(Transaction).where(Transaction.user_id == user_id).offset(skip).limit(limit)
    return session.exec(statement).all()

def get_transaction_by_id(session: Session, transaction_id: int) -> Optional[Transaction]:
    return session.get(Transaction, transaction_id)

def update_transaction(session: Session, db_transaction: Transaction, transaction_update: dict) -> Transaction:
    tag_ids = transaction_update.pop("tag_ids", None)
    for key, value in transaction_update.items():
        setattr(db_transaction, key, value)
    session.add(db_transaction)
    if tag_ids is not None:
        # Remove existing links
        links = session.exec(select(TransactionTagLink).where(TransactionTagLink.transaction_id == db_transaction.id)).all()
        for link in links:
            session.delete(link)
        # Add new links
        for tag_id in tag_ids:
            link = TransactionTagLink(transaction_id=db_transaction.id, tag_id=tag_id)
            session.add(link)
    session.commit()
    session.refresh(db_transaction)
    return db_transaction

def delete_transaction(session: Session, db_transaction: Transaction) -> None:
    session.delete(db_transaction)
    session.commit()

# Budget CRUD
def create_budget(session: Session, budget: BudgetCreate, user_id: int) -> Budget:
    db_budget = Budget(**budget.model_dump(), user_id=user_id)
    session.add(db_budget)
    session.commit()
    session.refresh(db_budget)
    return db_budget

def get_budgets_for_user(session: Session, user_id: int, skip: int = 0, limit: int = 100):
    statement = select(Budget).where(Budget.user_id == user_id).offset(skip).limit(limit)
    return session.exec(statement).all()

def get_budget_by_id(session: Session, budget_id: int) -> Optional[Budget]:
    return session.get(Budget, budget_id)

def update_budget(session: Session, db_budget: Budget, budget_update: dict) -> Budget:
    for key, value in budget_update.items():
        setattr(db_budget, key, value)
    session.add(db_budget)
    session.commit()
    session.refresh(db_budget)
    return db_budget

def delete_budget(session: Session, db_budget: Budget) -> None:
    session.delete(db_budget)
    session.commit()

# Tag CRUD
def get_tag_by_name_and_user(session: Session, name: str, user_id: int) -> Optional[Tag]:
    return session.exec(select(Tag).where(Tag.name == name, Tag.user_id == user_id)).first()

def create_tag(session: Session, tag: TagCreate, user_id: int) -> Tag:
    db_tag = Tag(**tag.model_dump(), user_id=user_id)
    session.add(db_tag)
    session.commit()
    session.refresh(db_tag)
    return db_tag

def get_tags_for_user(session: Session, user_id: int, skip: int = 0, limit: int = 100):
    statement = select(Tag).where(Tag.user_id == user_id).offset(skip).limit(limit)
    return session.exec(statement).all()

def get_tag_by_id(session: Session, tag_id: int) -> Optional[Tag]:
    return session.get(Tag, tag_id)

def update_tag(session: Session, db_tag: Tag, tag_update: dict) -> Tag:
    for key, value in tag_update.items():
        setattr(db_tag, key, value)
    session.add(db_tag)
    session.commit()
    session.refresh(db_tag)
    return db_tag

def delete_tag(session: Session, db_tag: Tag) -> None:
    session.delete(db_tag)
    session.commit()
