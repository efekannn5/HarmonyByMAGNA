"""
Harmony Control Tower - Database Connection
READ-ONLY connection to SQL Server
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import urllib.parse
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection string
def get_connection_string() -> str:
    username = os.getenv("DB_USERNAME")
    password = urllib.parse.quote_plus(os.getenv("DB_PASSWORD"))
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    database = os.getenv("DB_DATABASE")
    driver = urllib.parse.quote_plus(os.getenv("DB_DRIVER"))
    
    connection_string = (
        f"mssql+pyodbc://{username}:{password}@{host}:{port}/{database}"
        f"?driver={driver}&Encrypt=yes&TrustServerCertificate=yes"
    )
    
    return connection_string

# Create engine with connection pooling optimized for READ-ONLY
engine = create_engine(
    get_connection_string(),
    poolclass=NullPool,  # No connection pooling for READ-ONLY (reduce load)
    echo=False,
    connect_args={
        "timeout": 30,
        "autocommit": True  # READ-ONLY mode
    }
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection() -> bool:
    """Test database connection"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return result.fetchone()[0] == 1
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
