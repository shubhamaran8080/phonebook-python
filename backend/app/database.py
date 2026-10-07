import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# In Docker Compose the database host is "db"; locally use "localhost".
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://phonebook:phonebook@db:5432/phonebook",
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """Provide a database session for a request and close it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
