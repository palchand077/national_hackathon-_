import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration
# Set MYSQL_URL env var or DB credentials. Fallback to SQLite if MySQL is not available.
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB = os.getenv("MYSQL_DB", "smart_fir_360")

DEFAULT_MYSQL_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_MYSQL_URL)

SQLITE_FALLBACK_URL = f"sqlite:///{BASE_DIR}/smart_fir_360.db"

# JWT Auth Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "smart_fir_360_super_secret_jwt_key_hackathon_2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days

# File Uploads Directory
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
