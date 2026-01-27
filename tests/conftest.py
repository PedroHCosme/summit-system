import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.data.models import Base, Plano, Membro

# Use in-memory SQLite for speed and isolation
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    """Creates a fresh database for each test."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine) # Create tables
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Seed required data (e.g., Plans)
    plan = Plano(nome="Mensal", preco=100.0, ativo=True)
    session.add(plan)
    session.commit()
    
    yield session
    
    session.close()
