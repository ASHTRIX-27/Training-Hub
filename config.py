import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-this-in-prod'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///training_hub.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    BACKUP_FOLDER = os.path.join(os.getcwd(), 'backups')
    MAX_CONTENT_LENGTH = None  # Unlimited file size as requested (handled by web server config usually, but Flask helps)
