from app import create_app
from extensions import db
from models import User, Folder, File
import os

app = create_app()

with app.app_context():
    print("Checking database...")
    # Clean up test data if exists
    Folder.query.filter_by(name='Test Folder').delete()
    db.session.commit()

    # Create test user if needed
    user = User.query.first()
    if not user:
        print("No user found, cannot test file upload ownership.")
        exit(1)

    # Test Folder Creation
    print("Creating Folder...")
    folder = Folder(name='Test Folder')
    db.session.add(folder)
    db.session.commit()
    print(f"Folder created: {folder.id} - {folder.name}")

    # Test Subfolder
    print("Creating Subfolder...")
    subfolder = Folder(name='Sub Folder', parent=folder)
    db.session.add(subfolder)
    db.session.commit()
    print(f"Subfolder created: {subfolder.id} - parent: {subfolder.parent_id}")

    # Test File Creation (DB only)
    print("Creating File record...")
    f = File(filename='test.txt', path='test.txt', uploader_id=user.id, folder_id=folder.id)
    db.session.add(f)
    db.session.commit()
    print(f"File created: {f.id} in folder {f.folder.name}")

    # Test Relationships
    print(f"Folder 'Test Folder' has {len(folder.subfolders)} subfolders and {len(folder.files)} files.")
    
    if len(folder.subfolders) != 1 or len(folder.files) != 1:
        print("ERROR: Relationships not working as expected!")
    else:
        print("Relationships OK.")

    # Cleanup
    print("Cleaning up...")
    db.session.delete(f)
    db.session.delete(subfolder)
    db.session.delete(folder)
    db.session.commit()
    print("Done.")
