"""
Tests for tag endpoints.
"""


def test_create_tag(client, auth_headers):
    """Test creating a new tag."""
    tag_data = {
        "name": "groceries",
    }
    response = client.post("/tags/", json=tag_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == tag_data["name"]
    assert data["user_id"] is not None
    assert "id" in data
    assert "created_at" in data


def test_create_duplicate_tag_fails(client, auth_headers):
    """Creating a tag with duplicate name (same user) should fail."""
    tag_data = {"name": "duplicate"}
    response = client.post("/tags/", json=tag_data, headers=auth_headers)
    assert response.status_code == 201

    response = client.post("/tags/", json=tag_data, headers=auth_headers)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_get_tags_empty(client, auth_headers):
    """Test retrieving tags when none exist."""
    response = client.get("/tags/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_get_tags_with_items(client, auth_headers):
    """Test retrieving tags after creating one."""
    tag_data = {"name": "entertainment"}
    response = client.post("/tags/", json=tag_data, headers=auth_headers)
    assert response.status_code == 201

    response = client.get("/tags/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == tag_data["name"]


def test_get_tag_by_id(client, auth_headers):
    """Test retrieving a single tag by ID."""
    tag_data = {"name": "transport"}
    response = client.post("/tags/", json=tag_data, headers=auth_headers)
    assert response.status_code == 201
    created_tag = response.json()
    tag_id = created_tag["id"]

    response = client.get(f"/tags/{tag_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == tag_id
    assert data["name"] == tag_data["name"]


def test_update_tag(client, auth_headers):
    """Test updating an existing tag."""
    tag_data = {"name": "old"}
    response = client.post("/tags/", json=tag_data, headers=auth_headers)
    assert response.status_code == 201
    created_tag = response.json()
    tag_id = created_tag["id"]

    update_data = {"name": "updated"}
    response = client.patch(
        f"/tags/{tag_id}", json=update_data, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]


def test_delete_tag(client, auth_headers):
    """Test deleting a tag."""
    tag_data = {"name": "to delete"}
    response = client.post("/tags/", json=tag_data, headers=auth_headers)
    assert response.status_code == 201
    created_tag = response.json()
    tag_id = created_tag["id"]

    # Delete
    response = client.delete(f"/tags/{tag_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Tag deleted successfully"

    # Verify it's gone
    response = client.get(f"/tags/{tag_id}", headers=auth_headers)
    assert response.status_code == 404