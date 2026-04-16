"""SQLAlchemy database setup and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import settings


# SQLite requires check_same_thread=False for FastAPI's async usage
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, echo=settings.DEBUG)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


def get_db():
    """FastAPI dependency that yields a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables and bootstrap first admin. Called at application startup."""
    from models import user, analysis, scenario  # noqa: F401 – register models
    Base.metadata.create_all(bind=engine)
    _bootstrap_first_admin()


def _bootstrap_first_admin():
    """Promote user #1 to admin if no admin exists yet."""
    from models.user import User
    db = SessionLocal()
    try:
        admin_exists = db.query(User).filter(User.role == "admin").first()
        if admin_exists:
            return
        first_user = db.query(User).order_by(User.id).first()
        if first_user:
            first_user.role = "admin"
            db.commit()
    finally:
        db.close()
