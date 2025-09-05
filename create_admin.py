# create_admin.py
from app import app
from models import db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    username = "admin"
    password = "Adminpa$$"

    existing = User.query.filter_by(username=username).first()
    if existing:
        print("Admin already exists:", existing.username)
    else:
        admin = User(username=username, password=generate_password_hash(password), role='admin')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created. username:", username, "password:", password)
