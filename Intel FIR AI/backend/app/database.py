import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import OperationalError
from app.config import DATABASE_URL, SQLITE_FALLBACK_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smart_fir_360.db")

engine = None
SessionLocal = None
Base = declarative_base()

try:
    # Test connection to configured Database (MySQL)
    test_engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    with test_engine.connect() as conn:
        logger.info(f"Connected successfully to Primary Database: {DATABASE_URL}")
    engine = test_engine
except Exception as e:
    logger.warning(f"Could not connect to MySQL at {DATABASE_URL}: {e}")
    logger.info(f"Falling back to local SQLite engine: {SQLITE_FALLBACK_URL}")
    engine = create_engine(
        SQLITE_FALLBACK_URL, 
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
