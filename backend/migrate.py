"""
migrate.py  —  Run ONCE to add auth columns to existing SQLite database.
Usage:  python migrate.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'stroke_predictions.db')
# Try alternate path if instance/ folder isn't used
if not os.path.exists(DB_PATH):
    DB_PATH = os.path.join(os.path.dirname(__file__), 'stroke_predictions.db')

print(f"Using database: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()

def column_exists(table, column):
    cur.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())

def table_exists(table):
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cur.fetchone() is not None

# 1. Create users table if it doesn't exist
if not table_exists('users'):
    cur.execute("""
        CREATE TABLE users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ Created users table")
else:
    print("✓ users table already exists")

# 2. Add created_by to patient_predictions
if not column_exists('patient_predictions', 'created_by'):
    cur.execute("ALTER TABLE patient_predictions ADD COLUMN created_by TEXT DEFAULT 'system'")
    print("✓ Added created_by to patient_predictions")
else:
    print("✓ patient_predictions.created_by already exists")

# 3. Add created_by to batch_predictions
if not column_exists('batch_predictions', 'created_by'):
    cur.execute("ALTER TABLE batch_predictions ADD COLUMN created_by TEXT DEFAULT 'system'")
    print("✓ Added created_by to batch_predictions")
else:
    print("✓ batch_predictions.created_by already exists")

# 4. Create patients table if missing
if not table_exists('patients'):
    cur.execute("""
        CREATE TABLE patients (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id        TEXT UNIQUE NOT NULL,
            gender            TEXT,
            age               REAL,
            hypertension      INTEGER,
            heart_disease     INTEGER,
            ever_married      TEXT,
            work_type         TEXT,
            residence_type    TEXT,
            avg_glucose_level REAL,
            bmi               REAL,
            smoking_status    TEXT,
            created_at        DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ Created patients table")

# 5. Create prediction_history table if missing
if not table_exists('prediction_history'):
    cur.execute("""
        CREATE TABLE prediction_history (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id        TEXT NOT NULL,
            prediction_result TEXT,
            risk_score        REAL,
            confidence_score  TEXT,
            model_used        TEXT DEFAULT 'LightGBM',
            prediction_source TEXT DEFAULT 'single',
            created_at        DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ Created prediction_history table")

conn.commit()
conn.close()
print("\n✅ Migration complete. No existing data was modified.")