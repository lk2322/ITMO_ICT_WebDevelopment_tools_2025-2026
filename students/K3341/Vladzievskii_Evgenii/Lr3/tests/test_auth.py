"""
Tests for authentication endpoints.
"""
def test_register(client):
    """Test user registration."""
    user_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "securepassword123",
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "id" in data
    assert "hashed_password" not in data


def test_register_duplicate_username(client):
    """Test registration with duplicate username fails."""
    user_data = {
        "username": "duplicate",
        "email": "unique@example.com",
        "password": "password123",
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201

    # Try again with same username
    user_data2 = {
        "username": "duplicate",
        "email": "another@example.com",
        "password": "password456",
    }
    response = client.post("/auth/register", json=user_data2)
    assert response.status_code == 400
    assert "username" in response.json()["detail"].lower()


def test_login(client):
    """Test user login and token retrieval."""
    # First register
    user_data = {
        "username": "loginuser",
        "email": "login@example.com",
        "password": "mypassword",
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201

    # Login
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"],
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    """Test login with incorrect password fails."""
    user_data = {
        "username": "wrongpass",
        "email": "wrong@example.com",
        "password": "rightpassword",
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201

    login_data = {
        "username": user_data["username"],
        "password": "wrongpassword",
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_protected_endpoint_without_token(client):
    """Test accessing a protected endpoint without token returns 401."""
    response = client.get("/categories/")
    assert response.status_code == 401


def test_protected_endpoint_with_token(client, auth_headers):
    """Test accessing a protected endpoint with valid token succeeds."""
    response = client.get("/categories/", headers=auth_headers)
    # Should return empty list (no categories yet) or 200
    assert response.status_code == 200


def test_get_current_user_info(client, auth_headers):
    """Test getting current user info."""
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "hashed_password" not in data


def test_get_current_user_info_without_token(client):
    """Test getting current user info without token returns 401."""
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_get_users(client, auth_headers):
    """Test getting list of users."""
    response = client.get("/auth/users", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["username"] == "testuser"
    assert "hashed_password" not in data[0]


def test_change_password(client, auth_headers):
    """Test changing password."""
    change_data = {
        "old_password": "testpassword123",
        "new_password": "newpass456",
    }
    response = client.post("/auth/change-password", json=change_data, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Password changed successfully"

    # Verify can login with new password
    login_data = {"username": "testuser", "password": "newpass456"}
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_change_password_wrong_old(client, auth_headers):
    """Test changing password with wrong old password fails."""
    change_data = {
        "old_password": "wrongoldpass",
        "new_password": "newpass456",
    }
    response = client.post("/auth/change-password", json=change_data, headers=auth_headers)
    assert response.status_code == 400
    assert "incorrect" in response.json()["detail"].lower()
