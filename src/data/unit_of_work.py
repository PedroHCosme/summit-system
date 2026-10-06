"""Implementação SQLAlchemy do padrão Unit of Work."""

from sqlalchemy.orm import Session

from src.core.unit_of_work import AbstractUnitOfWork


class SqlaUnitOfWork(AbstractUnitOfWork):
    """Unit of Work que envolve uma sessão SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Expõe a sessão para queries analíticas que precisam de acesso direto."""
        return self._session

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
