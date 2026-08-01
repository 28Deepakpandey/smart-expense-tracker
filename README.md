# Smart Expense Tracker API

A small REST API for tracking personal expenses, built for the Diligent
Software Engineering Apprenticeship 2026 take-home assignment.

## Overview

The API lets a user add expenses, view them, filter them by category,
see totals (overall and per category), see totals grouped by month, and
delete expenses. Data is persisted to a local JSON file, so it survives
server restarts without requiring a database.

## Features

- Add an expense (`title`, `amount`, `category`, `date`)
- View all expenses
- Filter expenses by category
- Calculate the overall total and the total per category
- Delete an expense by id
- **Bonus:** monthly summary endpoint — total spend grouped by calendar month

## Project Structure

```
smart-expense-tracker/
├── README.md
├── AI_NOTES.md
├── requirements.txt
├── .gitignore
├── src/
│   ├── main.py        # FastAPI app and route handlers
│   ├── models.py       # Pydantic request/response models
│   ├── service.py      # Business logic (add/list/delete/summaries)
│   └── storage.py      # JSON file read/write layer
└── tests/
    ├── conftest.py     # Shared pytest fixtures (isolated test storage)
    └── test_expenses.py
```

## Installation

Requires Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate      # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Application

```bash
uvicorn src.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.
Interactive Swagger docs are available at `http://127.0.0.1:8000/docs`.

Expenses are stored in `expenses_data.json` at the project root, created
automatically on the first write.

## Running the Tests

```bash
pytest tests/ -v
```

All 16 tests were run against this exact command on a clean checkout
before submission and passed.

## API Endpoints

| Method | Endpoint                    | Description                                  |
|--------|------------------------------|-----------------------------------------------|
| POST   | `/expenses`                 | Add a new expense                             |
| GET    | `/expenses`                 | List all expenses (optional `?category=`)     |
| GET    | `/expenses/summary`         | Overall total and total by category           |
| GET    | `/expenses/summary/monthly` | Total spend grouped by month (bonus)          |
| DELETE | `/expenses/{expense_id}`    | Delete an expense by id                       |

## Example Requests and Responses

### Add an expense

```bash
curl -X POST http://127.0.0.1:8000/expenses \
  -H "Content-Type: application/json" \
  -d '{"title": "Groceries", "amount": 45.50, "category": "Food", "date": "2026-01-15"}'
```

```json
{
  "title": "Groceries",
  "amount": 45.5,
  "category": "Food",
  "date": "2026-01-15",
  "id": 1
}
```

### List all expenses

```bash
curl http://127.0.0.1:8000/expenses
```

```json
[
  {
    "title": "Groceries",
    "amount": 45.5,
    "category": "Food",
    "date": "2026-01-15",
    "id": 1
  },
  {
    "title": "Metro Card",
    "amount": 20.0,
    "category": "Transport",
    "date": "2026-01-18",
    "id": 2
  },
  {
    "title": "Movie Night",
    "amount": 12.75,
    "category": "Entertainment",
    "date": "2026-02-02",
    "id": 3
  }
]
```

### Filter by category

```bash
curl "http://127.0.0.1:8000/expenses?category=Food"
```

```json
[
  {
    "title": "Groceries",
    "amount": 45.5,
    "category": "Food",
    "date": "2026-01-15",
    "id": 1
  }
]
```

### Summary (overall + by category)

```bash
curl http://127.0.0.1:8000/expenses/summary
```

```json
{
  "total_overall": 78.25,
  "total_by_category": [
    { "category": "Entertainment", "total": 12.75 },
    { "category": "Food", "total": 45.5 },
    { "category": "Transport", "total": 20.0 }
  ]
}
```

### Monthly summary (bonus)

```bash
curl http://127.0.0.1:8000/expenses/summary/monthly
```

```json
[
  { "month": "2026-01", "total": 65.5 },
  { "month": "2026-02", "total": 12.75 }
]
```

### Delete an expense

```bash
curl -X DELETE http://127.0.0.1:8000/expenses/1
```

Returns `204 No Content` on success, or a `404` with a descriptive
message if the id does not exist:

```json
{
  "detail": "Expense with id 999 not found"
}
```

### Validation error

Invalid input (e.g. a non-positive amount) returns `422` with details
from FastAPI/Pydantic:

```json
{
  "detail": [
    {
      "type": "greater_than",
      "loc": ["body", "amount"],
      "msg": "Input should be greater than 0",
      "input": -5,
      "ctx": { "gt": 0.0 }
    }
  ]
}
```
