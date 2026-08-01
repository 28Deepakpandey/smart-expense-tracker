"""Tests for the Smart Expense Tracker API.

We cover the required functionality (add, list, filter, totals, delete)
plus validation and the bonus monthly-summary endpoint. Each test uses
the `client` fixture from conftest.py, which points at an isolated
temporary JSON file so tests never interfere with each other.
"""


def create_sample_expense(client, **overrides):
    """Helper: POST a valid expense, allowing individual fields to be overridden."""
    payload = {
        "title": "Groceries",
        "amount": 45.50,
        "category": "Food",
        "date": "2026-01-15",
    }
    payload.update(overrides)
    return client.post("/expenses", json=payload)


def test_create_expense_returns_201_with_assigned_id(client):
    response = create_sample_expense(client)
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["title"] == "Groceries"
    assert body["amount"] == 45.50
    assert body["category"] == "Food"
    assert body["date"] == "2026-01-15"


def test_create_expense_rejects_non_positive_amount(client):
    response = create_sample_expense(client, amount=0)
    assert response.status_code == 422


def test_create_expense_rejects_negative_amount(client):
    response = create_sample_expense(client, amount=-15)
    assert response.status_code == 422


def test_create_expense_rejects_blank_title(client):
    response = create_sample_expense(client, title="   ")
    assert response.status_code == 422


def test_create_expense_rejects_missing_field(client):
    response = client.post("/expenses", json={"title": "Coffee", "amount": 3.5})
    assert response.status_code == 422


def test_ids_increment_across_creates(client):
    first = create_sample_expense(client).json()
    second = create_sample_expense(client, title="Taxi").json()
    assert first["id"] == 1
    assert second["id"] == 2


def test_get_expenses_returns_all_created_expenses(client):
    create_sample_expense(client)
    create_sample_expense(client, title="Movie", category="Entertainment")

    response = client.get("/expenses")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_expenses_empty_list_when_none_created(client):
    response = client.get("/expenses")
    assert response.status_code == 200
    assert response.json() == []


def test_filter_expenses_by_category_is_case_insensitive(client):
    create_sample_expense(client, category="Food")
    create_sample_expense(client, title="Movie", category="Entertainment")

    # Stored as "Food", queried as lowercase "food" — should still match.
    response = client.get("/expenses", params={"category": "food"})
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["category"] == "Food"


def test_filter_by_unknown_category_returns_empty_list(client):
    create_sample_expense(client)
    response = client.get("/expenses", params={"category": "Travel"})
    assert response.status_code == 200
    assert response.json() == []


def test_summary_returns_overall_total_and_breakdown_by_category(client):
    create_sample_expense(client, amount=50, category="Food")
    create_sample_expense(client, title="Bus", amount=10, category="Transport")
    create_sample_expense(client, title="Snacks", amount=5, category="Food")

    response = client.get("/expenses/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["total_overall"] == 65  # 50 + 10 + 5
    by_category = {c["category"]: c["total"] for c in body["total_by_category"]}
    assert by_category == {"Food": 55, "Transport": 10}  # Food = 50 + 5


def test_summary_with_no_expenses_is_zero(client):
    response = client.get("/expenses/summary")
    assert response.status_code == 200
    assert response.json() == {"total_overall": 0, "total_by_category": []}


def test_monthly_summary_groups_totals_by_month(client):
    create_sample_expense(client, amount=20, date="2026-01-10")
    create_sample_expense(client, title="Rent", amount=500, date="2026-02-01")
    create_sample_expense(client, title="Snacks", amount=5, date="2026-01-20")

    response = client.get("/expenses/summary/monthly")
    assert response.status_code == 200
    totals_by_month = {item["month"]: item["total"] for item in response.json()}
    assert totals_by_month == {"2026-01": 25, "2026-02": 500}


def test_delete_expense_removes_it(client):
    created = create_sample_expense(client).json()

    response = client.delete(f"/expenses/{created['id']}")
    assert response.status_code == 204

    remaining = client.get("/expenses").json()
    assert remaining == []


def test_delete_nonexistent_expense_returns_404(client):
    response = client.delete("/expenses/999")
    assert response.status_code == 404
    # The error message should name the id that wasn't found, not just "404".
    assert "999" in response.json()["detail"]


def test_delete_only_removes_targeted_expense(client):
    first = create_sample_expense(client).json()
    second = create_sample_expense(client, title="Taxi").json()

    client.delete(f"/expenses/{first['id']}")

    remaining = client.get("/expenses").json()
    assert len(remaining) == 1
    assert remaining[0]["id"] == second["id"]
