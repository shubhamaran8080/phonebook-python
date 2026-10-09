"""Tests for the CSV import and export endpoints."""

import csv as csv_module
import io

from app.main import IMPORT_MAX_ROWS

CSV_HEADER = "name,phone_number,email,address"


def csv_body(rows):
    """Build a CSV string from a list of row tuples/lists."""
    lines = [CSV_HEADER]
    lines.extend(",".join(row) for row in rows)
    return "\n".join(lines) + "\n"


def import_csv(client, content, filename="contacts.csv"):
    return client.post(
        "/contacts/import",
        files={
            "file": (filename, io.BytesIO(content.encode("utf-8")), "text/csv")
        },
    )


def create_contact(client, name, phone, email=None, address=None):
    payload = {"name": name, "phone_number": phone}
    if email:
        payload["email"] = email
    if address:
        payload["address"] = address
    response = client.post("/contacts", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def parse_csv(text):
    return list(csv_module.reader(io.StringIO(text)))


# ---------------------------------------------------------------------------
# Import: success cases
# ---------------------------------------------------------------------------


def test_import_single_contact(client):
    response = import_csv(
        client,
        csv_body([["Rahul Sharma", "+919876543210", "rahul@example.com", "Pune"]]),
    )
    assert response.status_code == 200
    summary = response.json()
    assert summary["total"] == 1
    assert summary["imported"] == 1
    assert summary["failed"] == 0
    assert summary["duplicates"] == 0
    assert summary["errors"] == []

    contacts = client.get("/contacts").json()
    assert len(contacts) == 1
    assert contacts[0]["name"] == "Rahul Sharma"
    assert contacts[0]["phone_number"] == "+919876543210"
    assert contacts[0]["email"] == "rahul@example.com"
    assert contacts[0]["address"] == "Pune"


def test_import_multiple_contacts(client):
    rows = [
        ["A One", "+11111111111", "a.one@example.com", "City A"],
        ["B Two", "+22222222222", "b.two@example.com", "City B"],
        ["C Three", "+33333333333", "", ""],
    ]
    response = import_csv(client, csv_body(rows))
    assert response.status_code == 200
    summary = response.json()
    assert summary["total"] == 3
    assert summary["imported"] == 3
    assert summary["failed"] == 0
    assert summary["duplicates"] == 0

    contacts = client.get("/contacts").json()
    assert len(contacts) == 3
    # Empty optional cells are stored as NULL.
    assert contacts[2]["email"] is None
    assert contacts[2]["address"] is None


def test_import_minimal_columns(client):
    """email and address columns are optional."""
    response = import_csv(client, "name,phone_number\nRahul Sharma,+919876543210\n")
    assert response.status_code == 200
    summary = response.json()
    assert summary["imported"] == 1

    contact = client.get("/contacts").json()[0]
    assert contact["email"] is None
    assert contact["address"] is None


def test_import_preserves_existing_contacts(client):
    create_contact(client, "Existing User", "+919876543200", "existing@example.com")
    response = import_csv(
        client,
        csv_body([["New User", "+919876543210", "new@example.com", ""]]),
    )
    assert response.json()["imported"] == 1

    contacts = {c["phone_number"]: c["name"] for c in client.get("/contacts").json()}
    assert contacts["+919876543200"] == "Existing User"
    assert contacts["+919876543210"] == "New User"


# ---------------------------------------------------------------------------
# Import: duplicates
# ---------------------------------------------------------------------------


def test_import_duplicate_phone_number(client):
    create_contact(client, "Existing User", "+919876543210", "existing@example.com")
    response = import_csv(
        client,
        csv_body([["New User", "+919876543210", "new@example.com", "X"]]),
    )
    assert response.status_code == 200
    summary = response.json()
    assert summary["imported"] == 0
    assert summary["duplicates"] == 1
    assert summary["failed"] == 0

    # The existing contact is unchanged, nothing new was added.
    contacts = client.get("/contacts").json()
    assert len(contacts) == 1
    assert contacts[0]["name"] == "Existing User"


def test_import_duplicate_email(client):
    create_contact(client, "Existing User", "+919876543210", "same@example.com")
    response = import_csv(
        client,
        csv_body([["New User", "+919876543299", "same@example.com", ""]]),
    )
    summary = response.json()
    assert summary["imported"] == 0
    assert summary["duplicates"] == 1


def test_import_duplicate_within_same_file(client):
    rows = [
        ["First User", "+919876543210", "first@example.com", ""],
        ["Second User", "+919876543210", "second@example.com", ""],
    ]
    response = import_csv(client, csv_body(rows))
    summary = response.json()
    assert summary["imported"] == 1
    assert summary["duplicates"] == 1


# ---------------------------------------------------------------------------
# Import: validation errors
# ---------------------------------------------------------------------------


def test_import_invalid_email(client):
    response = import_csv(
        client,
        csv_body([["Bad Email", "+919876543210", "not-an-email", ""]]),
    )
    assert response.status_code == 200
    summary = response.json()
    assert summary["imported"] == 0
    assert summary["failed"] == 1
    assert summary["errors"][0]["row"] == 2
    assert any("email" in msg for msg in summary["errors"][0]["errors"])

    assert client.get("/contacts").json() == []


def test_import_invalid_phone_number(client):
    response = import_csv(client, csv_body([["Bad Phone", "12345", "", ""]]))
    summary = response.json()
    assert summary["failed"] == 1
    assert any("phone_number" in msg for msg in summary["errors"][0]["errors"])


def test_import_missing_name(client):
    response = import_csv(client, csv_body([["", "+919876543210", "", ""]]))
    summary = response.json()
    assert summary["failed"] == 1
    assert any("name" in msg for msg in summary["errors"][0]["errors"])


def test_import_partial_validation_errors(client):
    """Valid rows are imported even when other rows are invalid,
    and the invalid rows are reported with their row numbers."""
    rows = [
        ["Good User", "+919876543210", "good@example.com", ""],
        ["Bad Phone", "12345", "", ""],
        ["Another Good", "+919876543212", "another@example.com", ""],
    ]
    response = import_csv(client, csv_body(rows))
    summary = response.json()
    assert summary["total"] == 3
    assert summary["imported"] == 2
    assert summary["failed"] == 1
    # "Bad Phone" is on line 3 of the file.
    assert summary["errors"][0]["row"] == 3

    contacts = client.get("/contacts").json()
    assert len(contacts) == 2


# ---------------------------------------------------------------------------
# Import: malformed input and limits
# ---------------------------------------------------------------------------


def test_import_empty_file(client):
    response = import_csv(client, "")
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_import_headers_only(client):
    response = import_csv(client, CSV_HEADER + "\n")
    assert response.status_code == 200
    summary = response.json()
    assert summary["total"] == 0
    assert summary["imported"] == 0
    assert summary["failed"] == 0
    assert summary["duplicates"] == 0


def test_import_malformed_csv_missing_header(client):
    # Data rows without a header row.
    response = import_csv(client, "Rahul,+919876543210,rahul@example.com,Pune\n")
    assert response.status_code == 400
    assert "columns" in response.json()["detail"]


def test_import_invalid_encoding(client):
    response = client.post(
        "/contacts/import",
        files={"file": ("contacts.csv", io.BytesIO(b"\xff\xfe\x00\x00garbage"), "text/csv")},
    )
    assert response.status_code == 400
    assert "UTF-8" in response.json()["detail"]


def test_import_unsupported_file_type(client):
    response = import_csv(
        client,
        csv_body([["A", "+919876543210", "", ""]]),
        filename="contacts.txt",
    )
    assert response.status_code == 400
    assert "csv" in response.json()["detail"].lower()


def test_import_too_many_rows(client):
    rows = [
        [f"User {i}", f"+1555{i:010d}", f"user{i}@example.com", ""]
        for i in range(IMPORT_MAX_ROWS + 1)
    ]
    response = import_csv(client, csv_body(rows))
    assert response.status_code == 413
    assert "rows" in response.json()["detail"].lower()


def test_import_oversized_file(client):
    content = CSV_HEADER + "\n" + "x" * (5 * 1024 * 1024)
    response = import_csv(client, content)
    assert response.status_code == 413


# ---------------------------------------------------------------------------
# Import / export: authentication
# ---------------------------------------------------------------------------


def test_import_requires_authentication(api_client):
    content = csv_body([["A", "+919876543210", "", ""]])
    response = api_client.post(
        "/contacts/import",
        files={"file": ("contacts.csv", io.BytesIO(content.encode("utf-8")), "text/csv")},
    )
    assert response.status_code == 401


def test_export_requires_authentication(api_client):
    response = api_client.get("/contacts/export")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


def test_export_all_contacts_across_pages(client):
    """The export is not limited to one page of results."""
    for i in range(25):  # more than the default page size of 10
        create_contact(
            client,
            f"Export User {i:02d}",
            f"+919876{i:04d}",
            f"export{i}@example.com",
            f"City {i}",
        )

    response = client.get("/contacts/export")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]

    rows = parse_csv(response.content.decode("utf-8"))
    assert rows[0] == ["name", "phone_number", "email", "address"]
    assert len(rows) == 26  # header + 25 contacts
    names = {row[0] for row in rows[1:]}
    assert "Export User 00" in names
    assert "Export User 24" in names


def test_export_filtered_search_results(client):
    create_contact(client, "Rahul Sharma", "+919876543210", "rahul@example.com", "Pune")
    create_contact(client, "Amit Patil", "+919876543211", "amit@example.com", "Mumbai")
    create_contact(client, "Someone Else", "+919876543212", "else@example.com", "Delhi")

    response = client.get("/contacts/export", params={"q": "Rahul"})
    assert response.status_code == 200

    rows = parse_csv(response.content.decode("utf-8"))
    assert len(rows) == 2  # header + 1 match
    assert rows[1][0] == "Rahul Sharma"
    # Phone numbers are prefixed by the CSV-injection guard.
    assert rows[1][1] == "'+919876543210"
    assert rows[1][3] == "Pune"


def test_export_empty_result_set(client):
    response = client.get("/contacts/export", params={"q": "no-such-contact-xyz"})
    assert response.status_code == 200
    assert response.content.decode("utf-8") == "name,phone_number,email,address\n"


def test_export_csv_formula_injection_protection(client):
    create_contact(
        client,
        "=SUM(A1:A2)",
        "+919876543210",
        "test@example.com",
        "@cmd|' /C calc'!A0",
    )
    create_contact(
        client,
        "Minus User",
        "+919876543211",
        "minus@example.com",
        "-2+3",
    )
    create_contact(
        client,
        "Normal User",
        "+919876543212",
        "normal@example.com",
        "Plain Street 1",
    )

    response = client.get("/contacts/export")
    rows = parse_csv(response.content.decode("utf-8"))
    by_name = {row[0]: row for row in rows[1:]}

    # Dangerous values are prefixed with a single quote...
    assert by_name["'=SUM(A1:A2)"][1] == "'+919876543210"
    assert by_name["'=SUM(A1:A2)"][3] == "'@cmd|' /C calc'!A0"
    assert by_name["Minus User"][3] == "'-2+3"
    # ...while normal data is preserved as-is.
    assert by_name["Normal User"][3] == "Plain Street 1"
