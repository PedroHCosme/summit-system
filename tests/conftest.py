import pytest
import unicodedata
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from src.data.models import Base, Plano, Membro

# Use in-memory SQLite for speed and isolation
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    """Creates a fresh database for each test."""
    engine = create_engine(TEST_DATABASE_URL)
    
    def unaccent(text):
        if text is None:
            return None
        if not isinstance(text, str):
            text = str(text)
        return ''.join(c for c in unicodedata.normalize('NFD', text)
                       if unicodedata.category(c) != 'Mn')

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        dbapi_connection.create_function("unaccent", 1, unaccent)

    Base.metadata.create_all(bind=engine) # Create tables
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Seed required data (e.g., Plans)
    plan = Plano(nome="Mensal", preco=100.0, ativo=True)
    session.add(plan)
    session.commit()
    
    yield session
    
    session.close()
