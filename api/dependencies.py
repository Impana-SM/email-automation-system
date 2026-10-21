"""FastAPI dependency injection providers."""

from typing import Generator
from sqlalchemy.orm import Session
from db.database import get_db
from src.mailer import Mailer
from src.template_service import TemplateService

_mailer_instance = Mailer()
_template_service_instance = TemplateService()


def get_db_session() -> Generator[Session, None, None]:
    """Provides a database session yielding to the request context."""
    yield from get_db()


def get_mailer() -> Mailer:
    """Provides the singleton or configured Mailer instance."""
    return _mailer_instance


# Backward compatibility alias
get_email_service = get_mailer


def get_template_service() -> TemplateService:
    """Provides the TemplateService instance."""
    return _template_service_instance
