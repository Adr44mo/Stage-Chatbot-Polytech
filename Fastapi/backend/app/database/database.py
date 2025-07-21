from sqlmodel import create_engine, Session, SQLModel
from pathlib import Path
from typing import Generator

# Import color utilities
from color_utils import ColorPrint

cp = ColorPrint()

# Configuration SQLModel pour toutes les tables (auth + chat + RAG)
sqlite_file_path = Path(__file__).resolve().parent / "database.db"
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_path}"

# Engine SQLModel avec configuration optimisée
engine = create_engine(
    sqlite_url, 
    echo=False,  # Désactiver les logs SQL pour les performances
    connect_args={
        "check_same_thread": False,
        "timeout": 30
    }
)

def create_db_and_tables():
    """Créer toutes les tables SQLModel (auth + chat + RAG)"""
    SQLModel.metadata.create_all(engine)
    cp.print_success("[Database] Toutes les tables SQLModel créées avec succès")

def get_session() -> Generator[Session, None, None]:
    """Session SQLModel pour toutes les opérations de base de données"""
    with Session(engine) as session:
        yield session
