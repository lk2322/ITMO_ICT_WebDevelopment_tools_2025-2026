"""
Tests for budget endpoints.
"""
import datetime


def test_create_budget(client, auth_headers):
    """Test creating a new budget."""
    # Create a category (optional)
    category_data = {
        "name": "Groceries",
        "description": "Food",
        "type": "expense",
    }
    response = client.post("/categories/", json=category_data, headers=auth_headers)
    assert response.status_code == 201
    category = response.json()
    category_id = category["id"]

    budget_data = {
        "amount": 500.0,
        "period": "monthly",
        "start_date": datetime.datetime.utcnow().isoformat() + "Z",
        "end_date": None,
        "category_id": category_id,
    }
    response = client.post("/budgets/", json=budget_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == budget_data["amount"]
    assert data["period"] == budget_data["period"]
    assert data["category_id"] == category_id
    assert data["user_id"] is not None
    assert "id" in data
    assert "created_at" in data


def test_create_budget_without_category(client, auth_headers):
    """Test creating a budget without a category (global budget)."""
    budget_data = {
        "amount": 1000.0,
        "period": "monthly",
        "start_date": datetime.datetime.utcnow().isoformat() + "Z",
        "end_date": None,
        "category_id": None,
    }
    response = client.post("/budgets/", json=budget_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == budget_data["amount"]
    assert data["period"] == budget_data["period"]
    assert data["category_id"] is None


def test_get_budgets_empty(client, auth_headers):
    """Test retrieving budgets when none exist."""
    response = client.get("/budgets/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_get_budgets_with_items(client, auth_headers):
    """Test retrieving budgets after creating one."""
    budget_data = {
        "amount": 300.0,
        "period": "weekly",
        "start_date": datetime.datetime.utcnow().isoformat() + "Z",
        "end_date": None,
        "category_id": None,
    }
    response = client.post("/budgets/", json=budget_data, headers=auth_headers)
    assert response.status_code == 201

    response = client.get("/budgets/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["amount"] == budget_data["amount"]


def test_get_budget_by_id(client, auth_headers):
    """Test retrieving a single budget by ID."""
    budget_data = {
        "amount": 200.0,
        "period": "yearly",
        "start_date": datetime.datetime.utcnow().isoformat() + "Z",
        "end_date": None,
        "category_id": None,
    }
    response = client.post("/budgets/", json=budget_data, headers=auth_headers)
    assert response.status_code == 201
    created_budget = response.json()
    budget_id = created_budget["id"]

    response = client.get(f"/budgets/{budget_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == budget_id
    assert data["amount"] == budget_data["amount"]


def test_update_budget(client, auth_headers):
    """Test updating an existing budget."""
    budget_data = {
        "amount": 150.0,
        "period": "monthly",
        "start_date": datetime.datetime.utcnow().isoformat() + "Z",
        "end_date": None,
        "category_id": None,
    }
    response = client.post("/budgets/", json=budget_data, headers=auth_headers)
    assert response.status_code == 201
    created_budget = response.json()
    budget_id = created_budget["id"]

    update_data = {
        "amount": 200.0,
        "period": "weekly",
    }
    response = client.patch(
        f"/budgets/{budget_id}", json=update_data, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == update_data["amount"]
    assert data["period"] == update_data["period"]
    # other fields unchanged
    assert data["category_id"] is None


def test_delete_budget(client, auth_headers):
    """Test deleting a budget."""
    budget_data = {
        "amount": 99.99,
        "period": "monthly",
        "start_date": datetime.datetime.utcnow().isoformat() + "Z",
        "end_date": None,
        "category_id": None,
    }
    response = client.post("/budgets/", json=budget_data, headers=auth_headers)
    assert response.status_code == 201
    created_budget = response.json()
    budget_id = created_budget["id"]

    # Delete
    response = client.delete(f"/budgets/{budget_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Budget deleted successfully"

    # Verify it's gone
    response = client.get(f"/budgets/{budget_id}", headers=auth_headers)
    assert response.status_code == 404