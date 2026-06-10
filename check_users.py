from app import create_app
from extensions import db
from models import User

app = create_app()
with app.app_context():
    users = User.query.all()
    print(f"found {len(users)} users")
    for u in users:
        print(f"User: {u.username}, Role: {u.role}")
    
    if not users:
        print("No users found. Creating default admin.")
        admin = User(username='admin@example.com', role='super_admin')
        admin.set_password('password123')
        db.session.add(admin)
        db.session.commit()
        print("Created admin@example.com / password123")
