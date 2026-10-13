"""
create_users.py  —  Admin script to create application users.
Usage:  python create_users.py
"""
import bcrypt
import sqlite3
import os
import getpass

# Consistently target the instance database used by the Flask application
INSTANCE_DIR = os.path.join(os.path.dirname(__file__), 'instance')
os.makedirs(INSTANCE_DIR, exist_ok=True)
DB_PATH = os.path.join(INSTANCE_DIR, 'stroke_predictions.db')
if not os.path.exists(DB_PATH) and os.path.exists(os.path.join(os.path.dirname(__file__), 'stroke_predictions.db')):
    DB_PATH = os.path.join(os.path.dirname(__file__), 'stroke_predictions.db')

def _has_role_column(cur):
    cur.execute("PRAGMA table_info(users)")
    cols = [col[1] for col in cur.fetchall()]
    return 'role' in cols

def create_user(username, password, role='doctor'):
    pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    try:
        if _has_role_column(cur):
            cur.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, pw_hash, role)
            )
        else:
            cur.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, pw_hash)
            )
        conn.commit()
        print(f"✓ User '{username}' ({role}) created successfully in {os.path.basename(DB_PATH)}.")
    except sqlite3.IntegrityError:
        print(f"✗ Username '{username}' already exists.")
    finally:
        conn.close()

def list_users():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    has_role = _has_role_column(cur)
    if has_role:
        cur.execute("SELECT id, username, role, created_at FROM users")
    else:
        cur.execute("SELECT id, username, 'doctor', created_at FROM users")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        print("No users found.")
    else:
        print(f"\n{'ID':<5} {'Username':<15} {'Role':<10} {'Created At'}")
        print("-" * 55)
        for row in rows:
            print(f"{row[0]:<5} {row[1]:<15} {row[2]:<10} {row[3]}")

if __name__ == '__main__':
    print(f"=== NeuralStroke User Management ({os.path.basename(DB_PATH)}) ===\n")
    print("1. Create user")
    print("2. List users")
    choice = input("\nChoice (1/2): ").strip()

    if choice == '1':
        username = input("Username: ").strip()
        role     = input("Role (doctor/admin) [doctor]: ").strip().lower() or 'doctor'
        if role not in ('doctor', 'admin'):
            print(f"Unknown role '{role}', defaulting to 'doctor'")
            role = 'doctor'
        password = getpass.getpass("Password: ")
        confirm  = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("✗ Passwords do not match.")
        elif len(password) < 6:
            print("✗ Password must be at least 6 characters.")
        else:
            create_user(username, password, role)
    elif choice == '2':
        list_users()
    else:
        print("Invalid choice.")