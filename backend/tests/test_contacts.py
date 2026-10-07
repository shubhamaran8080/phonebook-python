import pytest

VALID_CONTACT = {
    "name": "John Doe",
    "phone_number": "+1234567890",
    "email": "john@example.com",
    "address": "123 Main St",
}


def test_create_contact(client):
    response = client.post("/contacts", json=VALID_CONTACT)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["phone_number"] == "+1234567890"
    assert data["email"] == "john@example.com"
    assert data["address"] == "123 Main St"
    assert "id" in data
    assert "created_at" in data


def test_create_contact_missing_required_name(client):
    payload = dict(VALID_CONTACT)
    del payload["name"]
    assert client.post("/contacts", json=payload).status_code == 422


def test_create_contact_invalid_phone_number(client):
    for bad in ["12345", "abc", "+0123456789", "+(123)456-7890"]:
        payload = dict(VALID_CONTACT, phone_number=bad)
        assert client.post("/contacts", json=payload).status_code == 422, bad


def test_create_contact_invalid_email(client):
    payload = dict(VALID_CONTACT, email="not-an-email")
    assert client.post("/contacts", json=payload).status_code == 422


def test_create_contact_duplicate_phone_number(client):
    assert client.post("/contacts", json=VALID_CONTACT).status_code == 201
    assert client.post("/contacts", json=VALID_CONTACT).status_code == 409


def test_create_contact_duplicate_email(client):
    assert client.post("/contacts", json=VALID_CONTACT).status_code == 201
    payload = dict(VALID_CONTACT, phone_number="+1987654321")
    assert client.post("/contacts", json=payload).status_code == 409


def test_list_contacts_pagination_and_search(client):
    for i in range(5):
        payload = {
            "name": f"User {i}",
            "phone_number": f"+1555{i:07d}",
            "email": f"user{i}@example.com",
        }
        assert client.post("/contacts", json=payload).status_code == 201

    # Pagination
    response = client.get("/contacts", params={"page": 1, "page_size": 2})
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.headers["X-Total-Count"] == "5"

    # Search by name
    response = client.get("/contacts", params={"q": "User 1"})
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["name"] == "User 1"

    # Search by phone number
    response = client.get("/contacts", params={"q": "15550000001"})
    assert len(response.json()) == 1


def test_get_contact(client):
    created = client.post("/contacts", json=VALID_CONTACT).json()
    response = client.get(f"/contacts/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_contact_not_found(client):
    assert client.get("/contacts/999").status_code == 404


def test_update_contact(client):
    created = client.post("/contacts", json=VALID_CONTACT).json()
    response = client.put(
        f"/contacts/{created['id']}",
        json={"name": "Jane Doe", "address": "456 Oak Ave"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Jane Doe"
    assert data["address"] == "456 Oak Ave"
    # Untouched fields keep their values
    assert data["phone_number"] == "+1234567890"
    assert data["email"] == "john@example.com"


def test_update_contact_not_found(client):
    assert client.put("/contacts/999", json={"name": "X"}).status_code == 404


def test_update_contact_duplicate_phone(client):
    first = client.post("/contacts", json=VALID_CONTACT).json()
    second = client.post(
        "/contacts",
        json={
            **VALID_CONTACT,
            "phone_number": "+1987654321",
            "email": "second@example.com",
        },
    ).json()
    response = client.put(
        f"/contacts/{second['id']}", json={"phone_number": first["phone_number"]}
    )
    assert response.status_code == 409


def test_delete_contact(client):
    created = client.post("/contacts", json=VALID_CONTACT).json()
    assert client.delete(f"/contacts/{created['id']}").status_code == 204
    assert client.get(f"/contacts/{created['id']}").status_code == 404
    assert client.delete(f"/contacts/{created['id']}").status_code == 404


def test_health_check(client):
    assert client.get("/health").json() == {"status": "ok"}
