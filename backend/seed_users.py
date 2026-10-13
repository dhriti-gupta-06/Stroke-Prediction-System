from app import app, init_default_users

with app.app_context():
    init_default_users()
    print("Demo users created successfully (safe mode)")