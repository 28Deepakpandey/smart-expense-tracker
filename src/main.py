"""FastAPI application entry point for the Smart Expense Tracker API.

Route handlers here are intentionally thin: they parse/validate the
request (via FastAPI + Pydantic), delegate to service.py for the actual
logic, and translate the result into an HTTP response. Business rules
live in service.py, not here, so they stay testable without HTTP.
"""
from typing import List, Optional

from fastapi import FastAPI, HTTPException, status

from src import service
from src.models import Expense, ExpenseCreate, ExpenseSummary, MonthlyTotal

app = FastAPI(
    title="Smart Expense Tracker API",
    description="A small REST API for tracking personal expenses.",
    version="1.0.0",
)


@app.post(
    "/expenses",
    response_model=Expense,
    status_code=status.HTTP_201_CREATED,  # 201, not 200 — a resource was created
    tags=["Expenses"],
    summary="Add a new expense",
)
def create_expense(payload: ExpenseCreate) -> Expense:
    # FastAPI has already validated `payload` against ExpenseCreate
    # (rejecting bad amounts/blank fields with a 422) before we get here.
    return service.add_expense(payload)


@app.get(
    "/expenses",
    response_model=List[Expense],
    tags=["Expenses"],
    summary="List expenses, optionally filtered by category",
)
def get_expenses(category: Optional[str] = None) -> List[Expense]:
    # `category` is an optional query parameter, e.g. GET /expenses?category=Food.
    # Omitting it returns every expense.
    return service.list_expenses(category=category)


@app.get(
    "/expenses/summary",
    response_model=ExpenseSummary,
    tags=["Summary"],
    summary="Overall total and total by category",
)
def get_summary() -> ExpenseSummary:
    return service.get_summary()


@app.get(
    "/expenses/summary/monthly",
    response_model=List[MonthlyTotal],
    tags=["Summary"],
    summary="Total spend grouped by month (bonus feature)",
)
def get_monthly_summary() -> List[MonthlyTotal]:
    return service.get_monthly_summary()


@app.delete(
    "/expenses/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,  # 204 — success, nothing to return
    tags=["Expenses"],
    summary="Delete an expense by id",
)
def remove_expense(expense_id: int) -> None:
    deleted = service.delete_expense(expense_id)
    if not deleted:
        # 404, with the id in the message, so a client immediately knows
        # which id it asked for that doesn't exist.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found",
        )
