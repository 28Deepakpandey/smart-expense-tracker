"""Business logic for managing expenses.

Kept separate from the FastAPI route handlers (main.py) so the
request/response layer stays thin, and so this logic can be unit
tested without going through HTTP at all if needed.
"""
from collections import defaultdict
from typing import Dict, List, Optional

from src import storage
from src.models import CategoryTotal, Expense, ExpenseCreate, ExpenseSummary, MonthlyTotal


def add_expense(payload: ExpenseCreate) -> Expense:
    """Create and persist a new expense, assigning it the next available id."""
    expenses = storage.load_expenses()
    expense = Expense(id=storage.next_id(expenses), **payload.model_dump())
    expenses.append(expense)
    storage.save_expenses(expenses)
    return expense


def list_expenses(category: Optional[str] = None) -> List[Expense]:
    """Return all expenses, optionally filtered by category (case-insensitive).

    Case-insensitive matching means a client filtering on `?category=food`
    still finds expenses stored as "Food" — a small usability choice that
    avoids surprising empty results from a capitalization mismatch.
    """
    expenses = storage.load_expenses()
    if category is None:
        return expenses
    return [e for e in expenses if e.category.lower() == category.lower()]


def delete_expense(expense_id: int) -> bool:
    """Delete an expense by id.

    Returns True/False rather than raising, so the route handler (which
    knows about HTTP status codes) decides how to respond — this
    function stays HTTP-agnostic.
    """
    expenses = storage.load_expenses()
    remaining = [e for e in expenses if e.id != expense_id]
    if len(remaining) == len(expenses):
        # Nothing was filtered out, so the id didn't exist.
        return False
    storage.save_expenses(remaining)
    return True


def get_summary() -> ExpenseSummary:
    """Compute the overall total and the total broken down by category."""
    expenses = storage.load_expenses()
    # round() avoids float noise like 65.50000000000001 leaking into
    # a money-related API response.
    total_overall = round(sum(e.amount for e in expenses), 2)

    totals_by_category: Dict[str, float] = defaultdict(float)
    for e in expenses:
        totals_by_category[e.category] += e.amount

    # Sorted alphabetically so the response order is stable and
    # predictable across requests, rather than depending on insertion
    # order or dict iteration order.
    by_category = [
        CategoryTotal(category=category, total=round(total, 2))
        for category, total in sorted(totals_by_category.items())
    ]
    return ExpenseSummary(total_overall=total_overall, total_by_category=by_category)


def get_monthly_summary() -> List[MonthlyTotal]:
    """Compute total spend grouped by calendar month (YYYY-MM). Bonus feature."""
    expenses = storage.load_expenses()
    totals_by_month: Dict[str, float] = defaultdict(float)
    for e in expenses:
        # date -> "YYYY-MM" groups by month regardless of the day, so
        # Jan 3rd and Jan 28th both roll up into the same "2026-01" bucket.
        month_key = e.date.strftime("%Y-%m")
        totals_by_month[month_key] += e.amount

    return [
        MonthlyTotal(month=month, total=round(total, 2))
        for month, total in sorted(totals_by_month.items())
    ]
