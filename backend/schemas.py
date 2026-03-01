"""Pydantic schemas for request and response validation."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

VALID_CATEGORIES = ["Food", "Transport", "Bills", "Fun", "Other"]
CATEGORY_PATTERN = "^(Food|Transport|Bills|Fun|Other)$"


class UserCreate(BaseModel):
    """Payload for user registration."""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)


class UserResponse(BaseModel):
    """Public user profile response."""

    id: int
    username: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    """Payload for user login."""

    username: str
    password: str


class ExpenseBase(BaseModel):
    """Shared fields for expense payloads."""

    title: str = Field(..., min_length=1, max_length=120)
    amount: float = Field(..., gt=0)
    category: str = Field(..., pattern=CATEGORY_PATTERN)
    date: date
    notes: Optional[str] = Field(default=None, max_length=500)


class ExpenseCreate(ExpenseBase):
    """Payload for creating an expense."""


class ExpenseUpdate(BaseModel):
    """Payload for updating an expense; all fields optional."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=120)
    amount: Optional[float] = Field(default=None, gt=0)
    category: Optional[str] = Field(default=None, pattern=CATEGORY_PATTERN)
    date: Optional[date] = None
    notes: Optional[str] = Field(default=None, max_length=500)


class ExpenseResponse(ExpenseBase):
    """Expense response model."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ExpenseSummary(BaseModel):
    """Aggregated spending statistics for dashboard rendering."""

    total_spending: float
    monthly_total: float
    average_daily_spending: float
    highest_spending_category: str
    category_totals: dict[str, float]
    monthly_breakdown: list[dict[str, float | str]]
