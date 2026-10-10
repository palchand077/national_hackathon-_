"""
SMART FIR 360 - MySQL Setup & Verification Script
Run this script if you have a local MySQL server (XAMPP / MySQL Workbench / Docker)
"""
import os
import pymysql
from pathlib import Path

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB = os.getenv("MYSQL_DB", "smart_fir_360")

def setup_mysql():
    print(f"Connecting to MySQL server at {MYSQL_HOST}:{MYSQL_PORT}...")
    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            autocommit=True
        )
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            print(f"✅ Database `{MYSQL_DB}` created or verified successfully!")
            
            schema_file = Path(__file__).parent / "schema.sql"
            if schema_file.exists():
                print(f"Applying schema from {schema_file.name}...")
                with open(schema_file, "r", encoding="utf-8") as f:
                    sql_statements = f.read().split(";")
                    for stmt in sql_statements:
                        stmt_clean = stmt.strip()
                        if stmt_clean:
                            cursor.execute(stmt_clean)
                print(f"✅ All MySQL tables and constraints created successfully!")
        conn.close()
    except Exception as e:
        print(f"⚠️ Could not connect to local MySQL server: {e}")
        print("Note: The SMART FIR 360 backend will automatically fall back to SQLite if MySQL is offline.")

if __name__ == "__main__":
    setup_mysql()
