"""Seed script for the Phonebook application.

Usage examples:

    # Create the initial demo user (password is prompted for if not given):
    python seed.py --create-user --username demo

    # Create a user with an explicit password (useful for Docker):
    python seed.py --create-user --username demo --password 'choose-a-password'

    # Generate dummy contacts:
    python seed.py --count 100
    python seed.py --count 1000
    python seed.py --count 5000

    # Combine both:
    python seed.py --create-user --username demo --count 1000

Generated contacts use Faker. Phone numbers and emails are generated
uniquely and existing contacts are never modified or duplicated.
"""

import argparse
import getpass
import os
import random

from faker import Faker

from app import models
from app.auth import get_password_hash
from app.database import SessionLocal, engine

BATCH_SIZE = 500


def create_user(db, username: str, password: str, email: str | None = None) -> None:
    """Create a new user with a bcrypt-hashed password."""
    existing = (
        db.query(models.User)
        .filter((models.User.username == username) | (models.User.email == email))
        .first()
    )
    if existing:
        print(f"User '{username}' already exists - nothing to do.")
        return
    db.add(
        models.User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
        )
    )
    db.commit()
    print(f"Created user '{username}'.")


def _random_phone() -> str:
    """A unique-looking E.164 phone number: '+1' followed by 10 digits."""
    return "+1" + str(random.randint(2000000000, 9999999999))


def generate_contacts(db, count: int) -> int:
    """Generate `count` dummy contacts without touching existing data."""
    fake = Faker()
    existing_phones = {row[0] for row in db.query(models.Contact.phone_number)}
    existing_emails = {
        row[0] for row in db.query(models.Contact.email) if row[0] is not None
    }
    used_phones = set(existing_phones)
    used_emails = set(existing_emails)

    batch = []
    created = 0
    attempts = 0
    while created < count and attempts < count * 20:
        attempts += 1

        phone = _random_phone()
        if phone in used_phones:
            continue

        email = fake.email().lower()
        while email in used_emails:
            email = f"{fake.user_name()}.{random.randint(1, 999999)}@example.com"

        used_phones.add(phone)
        used_emails.add(email)
        batch.append(
            models.Contact(
                name=fake.name(),
                phone_number=phone,
                email=email,
                address=fake.address().replace("\n", ", "),
            )
        )
        created += 1

        if len(batch) >= BATCH_SIZE:
            db.add_all(batch)
            db.commit()
            batch.clear()
            print(f"  ... {created}/{count} contacts created")

    if batch:
        db.add_all(batch)
        db.commit()
    print(f"Created {created} contacts (total in database may be higher).")
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the Phonebook database.")
    parser.add_argument(
        "--create-user",
        action="store_true",
        help="Create a demo user (requires --username)",
    )
    parser.add_argument("--username", help="Username for --create-user")
    parser.add_argument(
        "--password",
        help="Password for --create-user (prompted if omitted; SEED_PASSWORD env also works)",
    )
    parser.add_argument("--email", help="Optional email address for the demo user")
    parser.add_argument(
        "--count",
        type=int,
        default=0,
        help="Number of dummy contacts to generate (e.g. 100, 1000, 5000)",
    )
    args = parser.parse_args()

    if not args.create_user and not args.count:
        parser.error("Nothing to do: pass --create-user and/or --count")
    if args.create_user and not args.username:
        parser.error("--create-user requires --username")
    if args.count and not (1 <= args.count <= 50000):
        parser.error("--count must be between 1 and 50000")

    # Match the application's simple table-creation pattern.
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if args.create_user:
            password = (
                args.password
                or os.environ.get("SEED_PASSWORD")
                or getpass.getpass("Password for new user: ")
            )
            create_user(db, args.username, password, args.email)
        if args.count:
            generate_contacts(db, args.count)
    finally:
        db.close()


if __name__ == "__main__":
    main()
