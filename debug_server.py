from app import create_app
from models import User, Folder
from extensions import db

app = create_app()
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for testing

print("Starting full flow simulation...")
try:
    with app.test_client() as client:
        # 1. Login
        print("Logging in...")
        response = client.post('/login', data={'username': 'admin@example.com', 'password': 'password123'}, follow_redirects=True)
        print(f"Login Response Status: {response.status_code}")
        if b"Logout" not in response.data:
            print("FAILED: Could not log in. content excerpt:", response.data[:200])
        else:
            print("SUCCESS: Logged in.")

        # 2. Create Folder
        print("Creating Folder 'Debug Folder'...")
        response = client.post('/create_folder', data={'name': 'Debug Folder', 'parent_id': ''}, follow_redirects=True)
        print(f"Create Folder Response Status: {response.status_code}")
        
        # 3. Verify in DB
        with app.app_context():
            folder = Folder.query.filter_by(name='Debug Folder').first()
            if folder:
                print(f"SUCCESS: Folder 'Debug Folder' found in DB with ID {folder.id}.")
                db.session.delete(folder) # Clean up
                db.session.commit()
            else:
                print("FAILED: Folder not found in DB.")

        # 4. Verify Admin Access
        print("Accessing Admin Dashboard...")
        response = client.get('/admin/', follow_redirects=True)
        print(f"Admin Dashboard Status: {response.status_code}")
        if response.status_code == 200 and b"Admin Dashboard" in response.data:
             print("SUCCESS: Admin Dashboard accessed.")
        else:
             print("FAILED: Could not access Admin Dashboard.")
             
except Exception as e:
    print(f"EXCEPTION OCCURRED: {e}")
    import traceback
    traceback.print_exc()

