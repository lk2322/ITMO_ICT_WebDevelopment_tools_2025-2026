"""
Tests for category endpoints.
"""
def test_create_category(client, auth_headers):
    """Test creating a new category."""
    category_data = {
        "name": "Groceries",
        "description": "Food and household items",
        "type": "expense",
    }
    response = client.post("/categories/", json=category_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == category_data["name"]
    assert data["description"] == category_data["description"]
    assert data["type"] == category_data["type"]
    assert "id" in data
    assert "user_id" in data


def test_get_categories_empty(client, auth_headers):
    """Test retrieving categories when none exist."""
    response = client.get("/categories/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_get_categories_with_items(client, auth_headers):
    """Test retrieving categories after creating one."""
    category_data = {
        "name": "Entertainment",
        "description": "Movies, games, etc.",
        "type": "expense",
    }
    response = client.post("/categories/", json=category_data, headers=auth_headers)
    assert response.status_code == 201

    response = client.get("/categories/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == category_data["name"]


def test_get_category_by_id(client, auth_headers):
    """Test retrieving a single category by ID."""
    category_data = {
        "name": "Salary",
        "description": "Monthly income",
        "type": "income",
    }
    response = client.post("/categories/", json=category_data, headers=auth_headers)
    assert response.status_code == 201
    created_category = response.json()
    category_id = created_category["id"]

    response = client.get(f"/categories/{category_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == category_id
    assert data["name"] == category_data["name"]


def test_update_category(client, auth_headers):
    """Test updating an existing category."""
    category_data = {
        "name": "Old Name",
        "description": "Old description",
        "type": "expense",
    }
    response = client.post("/categories/", json=category_data, headers=auth_headers)
    assert response.status_code == 201
    created_category = response.json()
    category_id = created_category["id"]

    update_data = {
        "name": "Updated Name",
        "description": "Updated description",
        "type": "income",
    }
    response = client.patch(
        f"/categories/{category_id}", json=update_data, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    assert data["type"] == update_data["type"]


def test_delete_category(client, auth_headers):
    """Test deleting a category."""
    category_data = {
        "name": "To Delete",
        "description": "Will be deleted",
        "type": "expense",
    }
    response = client.post("/categories/", json=category_data, headers=auth_headers)
    assert response.status_code == 201
    created_category = response.json()
    category_id = created_category["id"]

    # Delete
    response = client.delete(f"/categories/{category_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Category deleted successfully"

    # Verify it's gone
    response = client.get(f"/categories/{category_id}", headers=auth_headers)
    assert response.status_code == 404