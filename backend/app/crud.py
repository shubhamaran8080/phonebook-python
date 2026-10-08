from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from . import models, schemas


def _apply_search(query, search):
    """Filter a Contact query by a search term (name or phone number)."""
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                models.Contact.name.ilike(like),
                models.Contact.phone_number.ilike(like),
            )
        )
    return query


def get_contacts(db: Session, *, skip: int = 0, limit: int = 100, search=None):
    return (
        _apply_search(db.query(models.Contact), search)
        .order_by(models.Contact.id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def count_contacts(db: Session, search=None) -> int:
    query = _apply_search(db.query(models.Contact), search)
    return query.with_entities(func.count(models.Contact.id)).scalar() or 0


def count_contacts_recent(db: Session, *, days: int = 7) -> int:
    """Contacts created within the last `days` days."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    return db.query(models.Contact).filter(models.Contact.created_at >= since).count()


def count_contacts_with_field(db: Session, field) -> int:
    return db.query(models.Contact).filter(field.isnot(None)).count()


def get_recent_contacts(db: Session, *, limit: int = 5):
    return (
        db.query(models.Contact)
        .order_by(models.Contact.created_at.desc(), models.Contact.id.desc())
        .limit(limit)
        .all()
    )


def get_contact(db: Session, contact_id: int):
    return db.query(models.Contact).filter(models.Contact.id == contact_id).first()


def create_contact(db: Session, contact: schemas.ContactCreate) -> models.Contact:
    db_contact = models.Contact(**contact.model_dump())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


def update_contact(db: Session, db_contact: models.Contact, updates: dict) -> models.Contact:
    for field, value in updates.items():
        setattr(db_contact, field, value)
    db.commit()
    db.refresh(db_contact)
    return db_contact


def delete_contact(db: Session, db_contact: models.Contact) -> None:
    db.delete(db_contact)
    db.commit()
