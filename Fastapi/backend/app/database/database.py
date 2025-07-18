from sqlmodel import create_engine, Session, SQLModel
from contextlib import contextmanager
from pathlib import Path

sqlite_file_path = Path(__file__).resolve().parent / "database.db"
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_path}"

engine = create_engine(sqlite_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

from sqlmodel import Session

def get_session():
    with Session(engine) as session:
        yield session
