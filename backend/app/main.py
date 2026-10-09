import csv
import io
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import auth as auth_utils, crud, models, schemas
from .database import engine, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (for the containerized setup; a migration tool
    # such as Alembic can replace this in production).
    models.Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Phonebook API", version="1.0.0", lifespan=lifespan)

# Allow the frontend (served separately) to call the API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@app.get("/contacts", response_model=list[schemas.ContactResponse], dependencies=[Depends(auth_utils.get_current_user)])
def list_contacts(
    response: Response,
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    q: str | None = Query(None, description="Search by name or phone number"),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    contacts = crud.get_contacts(db, skip=skip, limit=page_size, search=q)
    total = crud.count_contacts(db, search=q)

    # Pagination metadata in headers so the body stays a plain list.
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page"] = str(page)
    response.headers["X-Page-Size"] = str(page_size)
    return contacts


@app.post("/contacts", response_model=schemas.ContactResponse, status_code=201, dependencies=[Depends(auth_utils.get_current_user)])
def create_contact(contact: schemas.ContactCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_contact(db, contact)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A contact with this phone number or email already exists.",
        )


# ---------------------------------------------------------------------------
# CSV import / export
# ---------------------------------------------------------------------------

CSV_COLUMNS = ["name", "phone_number", "email", "address"]
IMPORT_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
IMPORT_MAX_ROWS = 5000


@app.post("/contacts/import", dependencies=[Depends(auth_utils.get_current_user)])
def import_contacts(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Import contacts from an uploaded UTF-8 CSV file.

    The CSV must contain `name` and `phone_number` columns;
    `email` and `address` are optional. Valid rows are inserted
    in a single transaction, duplicate phone numbers/emails are
    skipped and reported, and invalid rows are returned with
    their file row numbers and reasons.
    """
    filename = (file.filename or "").lower()
    if not filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files can be imported.")

    # Read at most the size limit (plus one extra byte) so that
    # oversized files are rejected without being fully loaded.
    content = file.file.read(IMPORT_MAX_BYTES + 1)
    if len(content) > IMPORT_MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"The CSV file is too large (maximum is "
            f"{IMPORT_MAX_BYTES // (1024 * 1024)} MB).",
        )

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="The CSV file must be UTF-8 encoded.")

    if not text.strip():
        raise HTTPException(status_code=400, detail="The CSV file is empty.")

    reader = csv.DictReader(io.StringIO(text))
    fieldnames = reader.fieldnames or []
    # Map the headers as written in the file to the canonical
    # field names (case-insensitive, whitespace-tolerant).
    column_map = {
        name: name.strip().lower()
        for name in fieldnames
        if name.strip().lower() in CSV_COLUMNS
    }
    if "name" not in column_map.values() or "phone_number" not in column_map.values():
        raise HTTPException(
            status_code=400,
            detail="The CSV must include 'name' and 'phone_number' columns.",
        )

    valid_rows = []
    errors = []
    for raw in reader:
        # reader.line_num is the actual line in the file (the
        # header is line 1), which is what we report to the user.
        row_number = reader.line_num
        if len(valid_rows) + len(errors) >= IMPORT_MAX_ROWS:
            raise HTTPException(
                status_code=413,
                detail=f"The CSV file has too many rows (maximum is {IMPORT_MAX_ROWS}).",
            )
        payload = {}
        for name, field in column_map.items():
            value = raw.get(name)
            value = value.strip() if isinstance(value, str) else ""
            # Empty optional cells are stored as NULL, like the web form.
            if value == "" and field in ("email", "address"):
                value = None
            payload[field] = value
        try:
            schemas.ContactCreate(**payload)
        except ValidationError as e:
            errors.append(
                {
                    "row": row_number,
                    "errors": [
                        f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
                        for err in e.errors()
                    ],
                }
            )
            continue
        valid_rows.append(payload)

    # Pre-check existing phone numbers and emails so duplicates are
    # reported instead of aborting the import (same approach as seed.py).
    used_phones = {row[0] for row in db.query(models.Contact.phone_number)}
    used_emails = {row[0] for row in db.query(models.Contact.email) if row[0]}

    imported = 0
    duplicates = 0
    for payload in valid_rows:
        phone = payload["phone_number"]
        email = payload.get("email")
        if phone in used_phones or (email is not None and email in used_emails):
            duplicates += 1
            continue
        db.add(models.Contact(**payload))
        used_phones.add(phone)
        if email is not None:
            used_emails.add(email)
        imported += 1

    # Single commit: either all valid, non-duplicate rows are stored
    # or (on a database error) nothing is stored.
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="The import was cancelled because of a duplicate phone number "
            "or email. No contacts were imported.",
        )

    return {
        "total": len(valid_rows) + len(errors),
        "imported": imported,
        "failed": len(errors),
        "duplicates": duplicates,
        "errors": errors,
    }


@app.get("/contacts/export", dependencies=[Depends(auth_utils.get_current_user)])
def export_contacts(
    q: str | None = Query(None, description="Export only contacts matching this search term"),
    db: Session = Depends(get_db),
):
    """Download all contacts (optionally filtered by a search term) as CSV.

    The export is streamed, is not limited to one page of results,
    and respects the current search term. Values that could be
    interpreted as formulas by spreadsheet applications are
    prefixed with a single quote (CSV injection protection).
    """

    def sanitize(value):
        if value and value[0] in ("=", "+", "-", "@"):
            return "'" + value
        return value or ""

    def generate():
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(CSV_COLUMNS)
        yield buffer.getvalue()
        for contact in crud.search_contacts(db, q):
            buffer.seek(0)
            buffer.truncate(0)
            writer.writerow(
                [
                    sanitize(contact.name),
                    sanitize(contact.phone_number),
                    sanitize(contact.email),
                    sanitize(contact.address),
                ]
            )
            yield buffer.getvalue()

    filename = f"phonebook-export-{datetime.now(timezone.utc).date().isoformat()}.csv"
    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/contacts/{contact_id}", response_model=schemas.ContactResponse, dependencies=[Depends(auth_utils.get_current_user)])
def get_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = crud.get_contact(db, contact_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@app.put("/contacts/{contact_id}", response_model=schemas.ContactResponse, dependencies=[Depends(auth_utils.get_current_user)])
def update_contact(
    contact_id: int, contact: schemas.ContactUpdate, db: Session = Depends(get_db)
):
    db_contact = crud.get_contact(db, contact_id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    try:
        return crud.update_contact(db, db_contact, contact.model_dump(exclude_unset=True))
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A contact with this phone number or email already exists.",
        )


@app.delete("/contacts/{contact_id}", status_code=204, dependencies=[Depends(auth_utils.get_current_user)])
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    db_contact = crud.get_contact(db, contact_id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    crud.delete_contact(db, db_contact)
    return None


# ---------------------------------------------------------------------------
# Authentication endpoints
# ---------------------------------------------------------------------------


@app.post("/auth/login")
def login(login_request: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Authenticate with a username or email and return a JWT access token."""
    identifier = login_request.username
    user = (
        db.query(models.User)
        .filter(
            (models.User.username == identifier) | (models.User.email == identifier)
        )
        .first()
    )
    if user is None or not auth_utils.verify_password(
        login_request.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=401, detail="Incorrect username/email or password"
        )
    token = auth_utils.create_access_token({"sub": user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": schemas.UserResponse.model_validate(user).model_dump(),
    }


@app.get("/auth/me")
def get_me(current_user: models.User = Depends(auth_utils.get_current_user)):
    """Return the currently authenticated user."""
    return schemas.UserResponse.model_validate(current_user)


@app.post("/auth/logout")
def logout():
    """Logout endpoint. JWTs are stateless, so the client discards its token."""
    return {"message": "Logged out"}


# ---------------------------------------------------------------------------
# Dashboard statistics
# ---------------------------------------------------------------------------


@app.get("/stats", response_model=schemas.StatsResponse, dependencies=[Depends(auth_utils.get_current_user)])
def get_stats(db: Session = Depends(get_db)):
    """Phonebook statistics for the dashboard."""
    return schemas.StatsResponse(
        total_contacts=crud.count_contacts(db),
        recent_contacts=crud.count_contacts_recent(db),
        with_email=crud.count_contacts_with_field(db, models.Contact.email),
        with_phone=crud.count_contacts_with_field(db, models.Contact.phone_number),
        recent_list=crud.get_recent_contacts(db),
    )
