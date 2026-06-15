"""
create_users.py  —  Admin script to create application users.
Usage:  python create_users.py
"""
import bcrypt
import sqlite3
import os
import getpass

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'stroke_predictions.db')
if not os.path.exists(DB_PATH):
    DB_PATH = os.path.join(os.path.dirname(__file__), 'stroke_predictions.db')

def create_user(username, password):
    pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, pw_hash)
        )
        conn.commit()
        print(f"✓ User '{username}' created successfully.")
    except sqlite3.IntegrityError:
        print(f"✗ Username '{username}' already exists.")
    finally:
        conn.close()

def list_users():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("SELECT id, username, created_at FROM users")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        print("No users found.")
    else:
        print(f"\n{'ID':<5} {'Username':<20} {'Created At'}")
        print("-" * 45)
        for row in rows:
            print(f"{row[0]:<5} {row[1]:<20} {row[2]}")

if __name__ == '__main__':
    print("=== NeuralStroke User Management ===\n")
    print("1. Create user")
    print("2. List users")
    choice = input("\nChoice (1/2): ").strip()

    if choice == '1':
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ")
        confirm  = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("✗ Passwords do not match.")
        elif len(password) < 6:
            print("✗ Password must be at least 6 characters.")
        else:
            create_user(username, password)
    elif choice == '2':
        list_users()
    else:
        print("Invalid choice.")