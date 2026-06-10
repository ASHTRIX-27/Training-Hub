from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False) # Email for standard users
    password_hash = db.Column(db.String(200))
    role = db.Column(db.String(20), nullable=False, default='user') # super_admin, admin, user, guest
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Guest specific
    guest_expires_at = db.Column(db.DateTime, nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_guest(self):
        return self.role == 'guest'
        
    @property
    def is_admin(self):
        return self.role in ['super_admin', 'admin']
        
    @property
    def is_super_admin(self):
        return self.role == 'super_admin'

    @property
    def is_expired(self):
        if self.role == 'guest' and self.guest_expires_at:
            return datetime.utcnow() > self.guest_expires_at
        return False

class Folder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_training = db.Column(db.Boolean, default=False)
    
    subfolders = db.relationship('Folder', backref=db.backref('parent', remote_side=[id]), lazy=True)
    files = db.relationship('File', backref='folder', lazy=True)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(500), nullable=False) # Relative to upload folder
    file_type = db.Column(db.String(50), nullable=True) # video, image, doc
    size = db.Column(db.Integer, nullable=True) # Bytes
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=True)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    uploader = db.relationship('User', backref='uploaded_files')

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Nullable in case user is deleted
    action = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User')

class AppConfig(db.Model):
    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.Text, nullable=True)

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='enrollments')
    folder = db.relationship('Folder', backref='enrollments')

class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='progress')
    file = db.relationship('File', backref='completions')

class FolderPermission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=False)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='folder_permissions')
    folder = db.relationship('Folder', backref='folder_permissions')
