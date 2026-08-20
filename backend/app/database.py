"""Session SQLAlchemy et base declarative."""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DATABASE_URL

_est_sqlite = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if _est_sqlite else {},
)

if _est_sqlite:

    @event.listens_for(engine, "connect")
    def _active_les_cles_etrangeres(dbapi_connection, connection_record):  # noqa: ARG001
        """SQLite n'applique PAS les cles etrangeres par defaut. Sans ceci, une
        suppression laisse des orphelins en silence."""
        curseur = dbapi_connection.cursor()
        curseur.execute("PRAGMA foreign_keys=ON")
        curseur.close()


SessionLocale = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocale()
    try:
        yield db
    finally:
        db.close()
