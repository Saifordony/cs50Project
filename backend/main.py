"""FastAPI backend for trackMoney expense tracker."""

from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

import auth
import models
import schemas
from database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="trackMoney API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def normalize_username(username: str) -> str:
    """Normalize username for consistent login/register behavior."""

    return username.strip().lower()


@app.get("/")
def root() -> dict[str, str]:
    """Health response for local development."""

    return {"message": "Welcome to trackMoney API"}


@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new account with hashed password."""

    normalized_username = normalize_username(user_data.username)
    existing_user = db.query(models.User).filter(models.User.username == normalized_username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    user = models.User(
        username=normalized_username,
        hashed_password=auth.get_password_hash(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/login", response_model=schemas.Token)
def login_user(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Authenticate and return bearer token."""

    normalized_username = normalize_username(login_data.username)
    user = db.query(models.User).filter(models.User.username == normalized_username).first()
    if not user or not auth.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/profile", response_model=schemas.UserResponse)
def get_profile(current_user: models.User = Depends(auth.get_current_user)):
    """Return current authenticated user profile."""

    return current_user


@app.get("/expenses", response_model=list[schemas.ExpenseResponse])
def list_expenses(
    sort_by: str = Query("date", pattern="^(date|amount)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    category: Optional[str] = Query(default=None, pattern=schemas.CATEGORY_PATTERN),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Return current user's expenses with filtering/sorting options."""

    query = db.query(models.Expense).filter(models.Expense.user_id == current_user.id)

    if category:
        query = query.filter(models.Expense.category == category)
    if start_date:
        query = query.filter(models.Expense.date >= start_date)
    if end_date:
        query = query.filter(models.Expense.date <= end_date)

    sort_column = models.Expense.date if sort_by == "date" else models.Expense.amount
    query = query.order_by(sort_column.asc() if order == "asc" else sort_column.desc())

    return query.all()


@app.post("/expenses", response_model=schemas.ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense_data: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Create a new expense for the current user."""

    expense = models.Expense(**expense_data.model_dump(), user_id=current_user.id)
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@app.put("/expenses/{expense_id}", response_model=schemas.ExpenseResponse)
def update_expense(
    expense_id: int,
    expense_data: schemas.ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Update one owned expense by ID."""

    expense = (
        db.query(models.Expense)
        .filter(models.Expense.id == expense_id, models.Expense.user_id == current_user.id)
        .first()
    )
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    updates = expense_data.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    for key, value in updates.items():
        setattr(expense, key, value)

    expense.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(expense)
    return expense


@app.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Delete one owned expense by ID."""

    expense = (
        db.query(models.Expense)
        .filter(models.Expense.id == expense_id, models.Expense.user_id == current_user.id)
        .first()
    )
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    db.delete(expense)
    db.commit()
    return None


@app.get("/expenses/summary", response_model=schemas.ExpenseSummary)
def get_expense_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Return aggregated statistics for dashboard cards/charts."""

    expenses = db.query(models.Expense).filter(models.Expense.user_id == current_user.id).all()
    if not expenses:
        return schemas.ExpenseSummary(
            total_spending=0,
            monthly_total=0,
            average_daily_spending=0,
            highest_spending_category="N/A",
            category_totals={},
            monthly_breakdown=[],
        )

    total_spending = sum(expense.amount for expense in expenses)
    current_month = datetime.utcnow().strftime("%Y-%m")
    monthly_total = sum(
        expense.amount for expense in expenses if expense.date.strftime("%Y-%m") == current_month
    )

    # Average daily spending across days that had entries.
    daily_totals: dict[date, float] = {}
    for expense in expenses:
        daily_totals[expense.date] = daily_totals.get(expense.date, 0) + expense.amount
    average_daily = sum(daily_totals.values()) / len(daily_totals)

    category_totals: dict[str, float] = {}
    for expense in expenses:
        category_totals[expense.category] = category_totals.get(expense.category, 0) + expense.amount

    top_category = max(category_totals, key=category_totals.get)

    month_rows = (
        db.query(func.strftime("%Y-%m", models.Expense.date).label("month"), func.sum(models.Expense.amount))
        .filter(models.Expense.user_id == current_user.id)
        .group_by("month")
        .order_by("month")
        .all()
    )
    monthly_breakdown = [{"month": row[0], "amount": float(row[1])} for row in month_rows]

    return schemas.ExpenseSummary(
        total_spending=round(total_spending, 2),
        monthly_total=round(monthly_total, 2),
        average_daily_spending=round(average_daily, 2),
        highest_spending_category=top_category,
        category_totals={k: round(v, 2) for k, v in category_totals.items()},
        monthly_breakdown=monthly_breakdown,
    )
