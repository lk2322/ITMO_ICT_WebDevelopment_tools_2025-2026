"""
Tests for transaction endpoints.
"""
import datetime


def test_create_transaction(client, auth_headers):
    """Test creating a new transaction."""
    # First create a category
    category_data = {
        "name": "Groceries",
        "description": "Food",
        "type": "expense",
    }
    response = client.post("/categories/", json=category_data, headers=auth_headers)
    assert response.status_code == 201
    category = response.json()
    category_id = category["id"]

    transaction_data = {
        "amount": 25.50,
        "description": "Weekly grocery shopping",
        "date": datetime.datetime.utcnow().isoformat() + "Z",
        "type": "expense",
        "category_id": category_id,
        "tag_ids": [],
    }
    response = client.post("/transactions/", json=transaction_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == transaction_data["amount"]
    assert data["description"] == transaction_data["description"]
    assert data["type"] == transaction_data["type"]
    assert data["category_id"] == category_id
    assert data["user_id"] is not None
    assert "id" in data
    assert "created_at" in data
    assert data["tags"] == []


def test_create_transaction_with_tags(client, auth_headers):
    """Test creating a transaction with tags."""
    # Create category
    category_data = {
        "name": "Entertainment",
        "description": "Movies",
        "type": "expense",
    }
    response = client.post("/categories/", json=category_data, headers=auth_headers)
    assert response.status_code == 201
    category_id = response.json()["id"]

    # Create tags
    tag1_data = {"name": "fun"}
    response = client.post("/tags/", json=tag1_data, headers=auth_headers)
    assert response.status_code == 201
    tag1_id = response.json()["id"]

    tag2_data = {"name": "weekend"}
    response = client.post("/tags/", json=tag2_data, headers=auth_headers)
    assert response.status_code == 201
    tag2_id = response.json()["id"]

    transaction_data = {
        "amount": 15.99,
        "description": "Movie ticket",
        "date": datetime.datetime.utcnow().isoformat() + "Z",
        "type": "expense",
        "category_id": category_id,
        "tag_ids": [tag1_id, tag2_id],
    }
    response = client.post("/transactions/", json=transaction_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == transaction_data["amount"]
    assert len(data["tags"]) == 2
    tag_names = {tag["name"] for tag in data["tags"]}
    assert tag_names == {"fun", "weekend"}


def test_get_transactions_empty(client, auth_headers):
    """Test retrieving transactions when none exist."""
    response = client.get("/transactions/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_get_transactions_with_items(client, auth_headers):
    """Test retrieving transactions after creating one."""
    # Create category
    category_data = {"name": "Food", "description": "", "type": "expense"}
    response = client.post("/categories/", json=category_data, headers=auth_headers)
    assert response.status_code == 201
    category_id = response.json()["id"]

    transaction_data = {
        "amount": 10.0,
        "description": "Lunch",
        "date": datetime.datetime.utcnow().isoformat() + "Z",
        "type": "expense",
        "category_id": category_id,
    }
    response = client.post("/transactions/", json=transaction_data, headers=auth_headers)
    assert response.status_code == 201

    response = client.get("/transactions/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["amount"] == transaction_data["amount"]


def test_get_transaction_by_id(client, auth_headers):
    """Test retrieving a single transaction by ID."""
    category_data = {"name": "Transport", "description": "", "type": "expense"}
    response = client.post("/categories/", json=category_data, headers=auth_headers)
    assert response.status_code == 201
    category_id = response.json()["id"]

    transaction_data = {
        "amount": 5.75,
        "description": "Bus fare",
        "date": datetime.datetime.utcnow().isoformat() + "Z",
        "type": "expense",
        "category_id": category_id,
    }
    response = client.post("/transactions/", json=transaction_data, headers=auth_headers)
    assert response.status_code == 201
    created_transaction = response.json()
    transaction_id = created_transaction["id"]

    response = client.get(f"/transactions/{transaction_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == transaction_id
    assert data["amount"] == transaction_data["amount"]


def test_update_transaction(client, auth_headers):
    """Test updating an existing transaction."""
    category_data = {"name": "Utilities", "description": "", "type": "expense"}
    response = client.post("/categories/", json=category_data, headers=auth_headers)
    assert response.status_code == 201
    category_id = response.json()["id"]

    transaction_data = {
        "amount": 100.0,
        "description": "Electricity",
        "date": datetime.datetime.utcnow().isoformat() + "Z",
        "type": "expense",
        "category_id": category_id,
    }
    response = client.post("/transactions/", json=transaction_data, headers=auth_headers)
    assert response.status_code == 201
    created_transaction = response.json()
    transaction_id = created_transaction["id"]

    update_data = {
        "amount": 120.0,
        "description": "Electricity bill",
    }
    response = client.patch(
        f"/transactions/{transaction_id}", json=update_data, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == update_data["amount"]
    assert data["description"] == update_data["description"]
    # other fields unchanged
    assert data["type"] == transaction_data["type"]
    assert data["category_id"] == category_id


def test_delete_transaction(client, auth_headers):
    """Test deleting a transaction."""
    category_data = {"name": "Misc", "description": "", "type": "expense"}
    response = client.post("/categories/", json=category_data, headers=auth_headers)
    assert response.status_code == 201
    category_id = response.json()["id"]

    transaction_data = {
        "amount": 1.99,
        "description": "Random",
        "date": datetime.datetime.utcnow().isoformat() + "Z",
        "type": "expense",
        "category_id": category_id,
    }
    response = client.post("/transactions/", json=transaction_data, headers=auth_headers)
    assert response.status_code == 201
    created_transaction = response.json()
    transaction_id = created_transaction["id"]

    # Delete
    response = client.delete(f"/transactions/{transaction_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Transaction deleted successfully"

    # Verify it's gone
    response = client.get(f"/transactions/{transaction_id}", headers=auth_headers)
    assert response.status_code == 404