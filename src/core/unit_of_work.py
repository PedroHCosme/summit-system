"""Padrão Unit of Work — interface abstrata."""

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Optional, Type


class AbstractUnitOfWork(ABC):
    """
    Gerencia o ciclo de vida de uma transação de banco de dados.

    Uso como context manager:
        with uow:
            uow.session.add(...)
            # commit automático no __exit__ sem exceção
        # rollback automático se exceção for lançada
    """

    @abstractmethod
    def commit(self) -> None:
        """Confirma a transação atual."""
        ...

    @abstractmethod
    def rollback(self) -> None:
        """Desfaz a transação atual."""
        ...

    def __enter__(self) -> "AbstractUnitOfWork":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
