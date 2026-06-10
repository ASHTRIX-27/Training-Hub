import os
import zipfile
import shutil
from datetime import datetime
from config import Config

def perform_backup(app):
    with app.app_context():
        # Source DB
        db_path = 'training_hub.db' # Default sqlite path often in root or instance
        # Config has SQLALCHEMY_DATABASE_URI, let's parse or assume default for this MVP
        if 'sqlite:///' in Config.SQLALCHEMY_DATABASE_URI:
            db_path = Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
            
        if not os.path.exists(db_path):
            print(f"Backup Error: DB file {db_path} not found.")
            return

        # Create Backup Dir
        backup_dir = Config.BACKUP_FOLDER
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        base_name = f"backup_{timestamp}"
        zip_path = os.path.join(backup_dir, f"{base_name}.zip")

        # Create Zip
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.write(db_path, os.path.basename(db_path))
        except Exception as e:
            print(f"Backup Failed: {e}")
            return

        # Split if > 1MB (1024 * 1024 bytes)
        MAX_SIZE = 1024 * 1024
        
        if os.path.getsize(zip_path) > MAX_SIZE:
             with open(zip_path, 'rb') as f:
                chunk_num = 1
                while True:
                    chunk = f.read(MAX_SIZE)
                    if not chunk:
                        break
                    
                    part_name = f"{base_name}.zip.{chunk_num:03d}"
                    part_path = os.path.join(backup_dir, part_name)
                    
                    with open(part_path, 'wb') as p:
                        p.write(chunk)
                    
                    chunk_num += 1
             
             # Remove original large zip
             os.remove(zip_path)
             print(f"Backup created and split into {chunk_num-1} parts.")
        else:
             print(f"Backup created successfully: {zip_path}")
