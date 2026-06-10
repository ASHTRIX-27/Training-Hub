from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import User, AppConfig, AuditLog
from extensions import db
from datetime import datetime, timedelta
import secrets
import string

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
@login_required
def require_admin():
    if not current_user.is_admin:
        flash("Access Denied: Admin only.", "danger")
        return redirect(url_for('main.index'))

@admin_bp.route('/')
def dashboard():
    users = User.query.filter(User.role != 'guest').all()
    guests = User.query.filter_by(role='guest').all()
    # clean expired guests
    now = datetime.utcnow()
    for guest in guests:
        if guest.is_expired:
             # Ideally delete, but for now just filter or mark (deletion task separates this)
             pass
             
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(50).all()
    from models import Folder
    training_folders = Folder.query.filter_by(is_training=True).all()
    
    return render_template('admin/dashboard.html', 
                         users=users, 
                         guests=guests, 
                         logs=logs,
                         training_folders=training_folders)

@admin_bp.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        email = request.form.get('email')
        # Simple password generation for now or manual input? User said "send emails out... with their user name and passwords"
        # So likely we generate one or let admin set it. Let's let admin set it for simplicity, or generate if empty.
        password = request.form.get('password')
        role = request.form.get('role', 'user')
        if not password:
             password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
             
        if User.query.filter_by(username=email).first():
            flash('User already exists.', 'danger')
            return redirect(url_for('admin.create_user'))
            
        new_user = User(username=email, role=role, created_by_id=current_user.id)
        new_user.set_password(password)
        db.session.add(new_user)
        
        # Log
        log = AuditLog(user_id=current_user.id, action='Create User', details=f'Created user {email}')
        db.session.add(log)
        db.session.commit()
        
        # TODO: Send Email (SMTP)
        flash(f'User created. Password: {password}', 'success')
        return redirect(url_for('admin.dashboard'))
        
    return render_template('admin/create_user.html')

@admin_bp.route('/create_guest', methods=['GET', 'POST'])
def create_guest():
    if request.method == 'POST':
        duration_val = int(request.form.get('duration_val'))
        duration_unit = request.form.get('duration_unit') # minutes, hours, days
        
        delta = timedelta()
        if duration_unit == 'minutes':
            delta = timedelta(minutes=duration_val)
        elif duration_unit == 'hours':
            delta = timedelta(hours=duration_val)
        elif duration_unit == 'days':
            delta = timedelta(days=duration_val)
            
        expires_at = datetime.utcnow() + delta
        
        username = f"Guest-{secrets.token_hex(4)}"
        password = secrets.token_urlsafe(8)
        
        guest = User(username=username, role='guest', guest_expires_at=expires_at, created_by_id=current_user.id)
        guest.set_password(password)
        
        db.session.add(guest)
        log = AuditLog(user_id=current_user.id, action='Create Guest', details=f'Created guest {username}, expires in {duration_val} {duration_unit}')
        db.session.add(log)
        db.session.commit()
        
        flash(f'Guest Account Created.\nUsername: {username}\nPassword: {password}\nExpires: {expires_at}', 'success')
        return redirect(url_for('admin.dashboard'))
        
    return render_template('admin/create_guest.html')

@admin_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        # Save SMTP settings
        configs = {
            'smtp_server': request.form.get('smtp_server'),
            'smtp_port': request.form.get('smtp_port'),
            'smtp_user': request.form.get('smtp_user'),
            'smtp_password': request.form.get('smtp_password')
        }
        
        for key, val in configs.items():
            conf = AppConfig.query.get(key)
            if not conf:
                conf = AppConfig(key=key)
                db.session.add(conf)
            conf.value = val
            
        log = AuditLog(user_id=current_user.id, action='Update Settings', details='Updated SMTP configuration')
        db.session.add(log)
        db.session.commit()
        flash('Settings updated.', 'success')
        
    # Load current settings
    configs = {c.key: c.value for c in AppConfig.query.all()}
    
    # Data for Folder Permissions
    from models import Folder, FolderPermission
    all_users = User.query.filter(User.role != 'super_admin').all()
    all_folders = Folder.query.all()
    
    # Map permissions: {user_id: [folder_id, ...]}
    permissions = {}
    for p in FolderPermission.query.all():
        if p.user_id not in permissions:
            permissions[p.user_id] = []
        permissions[p.user_id].append(p.folder_id)

    return render_template('admin/settings.html', 
                         settings=configs, 
                         users=all_users, 
                         folders=all_folders,
                         permissions=permissions)

@admin_bp.route('/settings/permissions', methods=['POST'])
def update_folder_permissions():
    from models import FolderPermission
    
    user_id = request.form.get('user_id')
    folder_ids = request.form.getlist('folders') # List of folder IDs to grant access to
    
    if user_id:
        # Clear existing
        FolderPermission.query.filter_by(user_id=user_id).delete()
        
        # Add new
        for fid in folder_ids:
            perm = FolderPermission(user_id=user_id, folder_id=int(fid))
            db.session.add(perm)
        
        db.session.commit()
        flash('Permissions updated successfully.', 'success')
        
    return redirect(url_for('admin.settings'))

@admin_bp.route('/enroll', methods=['POST'])
def enroll_user():
    user_id = request.form.get('user_id')
    folder_id = request.form.get('folder_id')
    
    if user_id and folder_id:
        from models import Enrollment
        existing = Enrollment.query.filter_by(user_id=user_id, folder_id=folder_id).first()
        if not existing:
            enrollment = Enrollment(user_id=user_id, folder_id=folder_id)
            db.session.add(enrollment)
            db.session.commit()
            flash('User enrolled successfully.', 'success')
        else:
            flash('User already enrolled in this training.', 'info')
            
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_super_admin:
        flash('Cannot delete Super Admin.', 'danger')
        return redirect(url_for('admin.dashboard'))
        
    db.session.delete(user)
    log = AuditLog(user_id=current_user.id, action='Delete User', details=f'Deleted user {user.username}')
    db.session.add(log)
    db.session.commit()
    flash('User deleted.', 'success')
    return redirect(url_for('admin.dashboard'))
