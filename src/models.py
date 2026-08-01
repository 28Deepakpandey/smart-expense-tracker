"""Pydantic models for the expense tracker API.

Splitting `ExpenseCreate` (the input shape) from `Expense` (the stored/
returned shape, which adds `id`) means the API never lets a client set
their own id on creation — the server always assigns it in service.py.
"""
from datetime import date as date_type
from typing import List

from pydantic import BaseModel, Field, field_validator


class ExpenseCreate(BaseModel):
    """Payload accepted when creating a new expense (no id yet)."""

    title: str = Field(..., min_length=1, max_length=200, description="Short description of the expense")
    # `gt=0` rejects zero and negative amounts at the validation layer, so
    # invalid data never reaches the storage/business logic below.
    amount: float = Field(..., gt=0, description="Expense amount, must be greater than zero")
    category: str = Field(..., min_length=1, max_length=50, description="Expense category, e.g. 'Food'")
    # Pydantic parses/validates this as a real date (not just any string),
    # so "2026-13-40" is rejected with a 422 before it ever hits our code.
    date: date_type = Field(..., description="Date the expense was incurred (YYYY-MM-DD)")

    @field_validator("title", "category")
    @classmethod
    def not_blank(cls, value: str) -> str:
        """Reject titles/categories that are empty once whitespace is stripped.

        `min_length=1` above only blocks an empty string; it would still
        accept "   " (whitespace only). This validator closes that gap.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class Expense(ExpenseCreate):
    """An expense as stored and returned by the API.

    Inherits every field from ExpenseCreate and adds the server-assigned id.
    """

    id: int


class CategoryTotal(BaseModel):
    """Total amount spent within a single category."""

    category: str
    total: float


class ExpenseSummary(BaseModel):
    """Response shape for GET /expenses/summary."""

    total_overall: float
    total_by_category: List[CategoryTotal]


class MonthlyTotal(BaseModel):
    """Total amount spent within a single calendar month (bonus feature)."""

    month: str  # YYYY-MM, e.g. "2026-01"
    total: float
