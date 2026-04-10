import os
from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv

load_dotenv()

# Database URL from environment variable, default to PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://finance:finance123@localhost:5432/finance_db")

# SQLite requires connect_args for multithreading support
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

# Create engine
engine = create_engine(DATABASE_URL, echo=True, connect_args=connect_args)

def init_db():
    """Create all tables."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Dependency to get database session."""
    with Session(engine) as session:
        yield session
