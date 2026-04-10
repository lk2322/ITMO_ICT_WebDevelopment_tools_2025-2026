from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from app.models import TransactionType, BudgetPeriod


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None


class ChangePassword(BaseModel):
    old_password: str
    new_password: str


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None


# Category schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: TransactionType

class CategoryCreate(CategoryBase):
    pass

class CategoryRead(CategoryBase):
    id: int
    user_id: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[TransactionType] = None


# Transaction schemas
class TransactionBase(BaseModel):
    amount: float
    description: Optional[str] = None
    date: datetime
    type: TransactionType
    category_id: int

class TransactionCreate(TransactionBase):
    tag_ids: Optional[list[int]] = []

class TransactionRead(TransactionBase):
    id: int
    user_id: int
    created_at: datetime
    tags: list["TagRead"] = []

    model_config = ConfigDict(from_attributes=True)

class TransactionUpdate(BaseModel):
    amount: Optional[float] = None
    description: Optional[str] = None
    date: Optional[datetime] = None
    type: Optional[TransactionType] = None
    category_id: Optional[int] = None
    tag_ids: Optional[list[int]] = None


# Budget schemas
class BudgetBase(BaseModel):
    amount: float
    period: BudgetPeriod
    start_date: datetime
    end_date: Optional[datetime] = None
    category_id: Optional[int] = None

class BudgetCreate(BudgetBase):
    pass

class BudgetRead(BudgetBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class BudgetUpdate(BaseModel):
    amount: Optional[float] = None
    period: Optional[BudgetPeriod] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    category_id: Optional[int] = None


# Tag schemas
class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class TagRead(TagBase):
    id: int
    user_id: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TagUpdate(BaseModel):
    name: Optional[str] = None


# Update forward references
TransactionRead.model_rebuild()
