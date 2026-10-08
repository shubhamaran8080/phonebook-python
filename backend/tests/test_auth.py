from app import auth as auth_utils
from app import models


def _create_user(db_session, username="alice", password="secret123", email="alice@example.com"):
    user = models.User(
        username=username,
        email=email,
        hashed_password=auth_utils.get_password_hash(password),
    )
    db_session.add(user)
    db_session.commit()
    return user


def _login(api_client, username="alice", password="secret123"):
    return api_client.post(
        "/auth/login", json={"username": username, "password": password}
    )


def _auth_headers(api_client, db_session, username="alice", password="secret123"):
    _create_user(db_session, username=username, password=password)
    response = _login(api_client, username=username, password=password)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


def test_login_success_with_username(api_client, db_session):
    _create_user(db_session)
    response = _login(api_client)
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"]["username"] == "alice"
    assert "hashed_password" not in data["user"]


def test_login_success_with_email(api_client, db_session):
    _create_user(db_session)
    response = _login(api_client, username="alice@example.com")
    assert response.status_code == 200
    assert response.json()["user"]["username"] == "alice"


def test_login_wrong_password(api_client, db_session):
    _create_user(db_session)
    response = _login(api_client, password="wrong")
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username/email or password"


def test_login_unknown_user(api_client):
    response = _login(api_client, username="nobody")
    assert response.status_code == 401


def test_login_validation(api_client):
    response = api_client.post("/auth/login", json={"username": "", "password": ""})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Token handling
# ---------------------------------------------------------------------------


def test_me_requires_token(api_client):
    assert api_client.get("/auth/me").status_code == 401


def test_me_with_token(api_client, db_session):
    headers = _auth_headers(api_client, db_session)
    response = api_client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"


def test_me_with_invalid_token(api_client):
    response = api_client.get("/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert response.status_code == 401


def test_logout_endpoint(api_client):
    assert api_client.post("/auth/logout").status_code == 200


# ---------------------------------------------------------------------------
# Protected contact APIs
# ---------------------------------------------------------------------------


def test_contacts_require_authentication(api_client):
    assert api_client.get("/contacts").status_code == 401
    assert api_client.post("/contacts", json={}).status_code == 401
    assert api_client.get("/contacts/1").status_code == 401
    assert api_client.put("/contacts/1", json={}).status_code == 401
    assert api_client.delete("/contacts/1").status_code == 401
    assert api_client.get("/stats").status_code == 401


def test_contacts_work_with_token(api_client, db_session):
    headers = _auth_headers(api_client, db_session)
    response = api_client.get("/contacts", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# Stats endpoint
# ---------------------------------------------------------------------------


def test_stats_with_token(api_client, db_session):
    headers = _auth_headers(api_client, db_session)
    api_client.post(
        "/contacts",
        headers=headers,
        json={
            "name": "Alice Smith",
            "phone_number": "+1234567890",
            "email": "alice@example.com",
        },
    )
    response = api_client.get("/stats", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_contacts"] == 1
    assert data["with_email"] == 1
    assert data["with_phone"] == 1
    assert data["recent_contacts"] >= 1
    assert len(data["recent_list"]) == 1
    assert data["recent_list"][0]["name"] == "Alice Smith"
