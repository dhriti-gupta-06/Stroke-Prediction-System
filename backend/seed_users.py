from app import app, db, User
import bcrypt

with app.app_context():

    users = [
        ("doctor1", "pass123"),
        ("doctor2", "pass456"),
        ("admin", "admin123")
    ]

    for username, password in users:

        # check if user already exists
        existing = User.query.filter_by(username=username).first()

        if existing:
            continue  # skip duplicates

        hashed_pw = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        )

        user = User(
            username=username,
            password_hash=hashed_pw.decode('utf-8')
        )

        db.session.add(user)

    db.session.commit()

    print("Demo users created successfully (safe mode)")