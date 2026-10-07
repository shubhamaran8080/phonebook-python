from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import crud, models, schemas
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


@app.get("/contacts", response_model=list[schemas.ContactResponse])
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


@app.post("/contacts", response_model=schemas.ContactResponse, status_code=201)
def create_contact(contact: schemas.ContactCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_contact(db, contact)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A contact with this phone number or email already exists.",
        )


@app.get("/contacts/{contact_id}", response_model=schemas.ContactResponse)
def get_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = crud.get_contact(db, contact_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@app.put("/contacts/{contact_id}", response_model=schemas.ContactResponse)
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


@app.delete("/contacts/{contact_id}", status_code=204)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    db_contact = crud.get_contact(db, contact_id)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    crud.delete_contact(db, db_contact)
    return None
