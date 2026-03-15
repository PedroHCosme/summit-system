"""
Configuração do SQLAlchemy para conexão com o banco de dados.

Este módulo fornece o engine e session factory para interagir com o banco
de dados usando SQLAlchemy ORM, oferecendo type safety e melhor manutenibilidade.
"""

import os
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base

# Base declarativa para os modelos ORM
Base = declarative_base()

# Caminho padrão do banco de dados (raiz do projeto)
_PROJECT_ROOT = Path(__file__).parent.parent.parent
from src.config import DB_FILENAME
_DEFAULT_DB_PATH = _PROJECT_ROOT / DB_FILENAME

# Engine singleton (lazy initialization)
_engine = None
_SessionLocal = None


def get_database_url(db_path: str = None) -> str:
    """
    Retorna a URL de conexão do SQLAlchemy para SQLite.
    
    Args:
        db_path: Caminho opcional para o arquivo do banco de dados.
                 Se None, usa o caminho padrão do projeto.
    
    Returns:
        URL de conexão no formato sqlite:///path/to/db
    """
    if db_path is None:
        db_path = str(_DEFAULT_DB_PATH)
    return f"sqlite:///{db_path}"


def get_engine(db_path: str = None):
    """
    Retorna o engine SQLAlchemy (singleton).
    
    O engine é reutilizado em toda a aplicação para gerenciar
    o pool de conexões com o banco de dados.
    
    Args:
        db_path: Caminho opcional para o arquivo do banco de dados.
    
    Returns:
        SQLAlchemy Engine
    """
    global _engine
    
    if _engine is None:
        database_url = get_database_url(db_path)
        _engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},  # Necessário para SQLite com threads
            echo=False  # True para debugging SQL
        )
        
        import unicodedata

        def unaccent(text):
            if text is None:
                return None
            if not isinstance(text, str):
                text = str(text)
            return ''.join(c for c in unicodedata.normalize('NFD', text)
                          if unicodedata.category(c) != 'Mn')

        # Habilitar foreign keys no SQLite (desabilitado por padrão)
        # E registrar função unaccent
        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
            
            # Registrar função unaccent
            dbapi_connection.create_function("unaccent", 1, unaccent)
    
    return _engine


def get_session_factory():
    """
    Retorna o factory de sessões SQLAlchemy.
    
    Returns:
        sessionmaker configurado para criar sessões
    """
    global _SessionLocal
    
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine()
        )
    
    return _SessionLocal


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager para obter uma sessão do banco de dados.
    
    Uso:
        with get_db_session() as session:
            # usar session aqui
            member = session.query(Membro).filter_by(id=1).first()
    
    A sessão é automaticamente fechada ao sair do contexto.
    Em caso de exceção, faz rollback automaticamente.
    
    Yields:
        Session: Sessão SQLAlchemy ativa
    """
    SessionLocal = get_session_factory()
    session = SessionLocal()
    
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_session() -> Session:
    """
    Cria uma nova sessão do banco de dados.
    
    IMPORTANTE: O chamador é responsável por fazer commit/rollback
    e fechar a sessão quando terminar.
    
    Para a maioria dos casos, prefira usar `get_db_session()` como
    context manager.
    
    Returns:
        Session: Nova sessão SQLAlchemy
    """
    SessionLocal = get_session_factory()
    return SessionLocal()


def init_db():
    """
    Inicializa o banco de dados criando todas as tabelas.
    
    Esta função cria as tabelas definidas nos modelos SQLAlchemy
    se elas ainda não existirem.
    """
    from src.data.models import Base  # Import para registrar os modelos
    Base.metadata.create_all(bind=get_engine())


def reset_engine():
    """
    Reseta o engine e session factory (útil para testes).
    """
    global _engine, _SessionLocal
    
    if _engine is not None:
        _engine.dispose()
    
    _engine = None
    _SessionLocal = None
