from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app
from flask_login import login_required, current_user
from models import User, File, Folder, AuditLog
from extensions import db
from utils import get_file_type, human_readable_size
import os
import uuid
from werkzeug.utils import secure_filename
from sqlalchemy import or_

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index_redirect():
    return redirect(url_for('main.dashboard'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_expired:
        flash('Account expired.', 'danger')
        return redirect(url_for('auth.logout'))
    
    # Statistics
    total_users = User.query.count()
    total_guests = User.query.filter_by(role='guest').count()
    total_files = File.query.count()
    total_videos = File.query.filter_by(file_type='video').count()
    total_images = File.query.filter_by(file_type='image').count()
    
    users_list = User.query.filter(User.role != 'guest').all()
    guests_list = User.query.filter_by(role='guest').all()
    
    return render_template('main/home.html', 
                         total_users=total_users,
                         total_guests=total_guests,
                         total_files=total_files,
                         total_videos=total_videos,
                         total_images=total_images,
                         users=users_list,
                         guests=guests_list)

@main_bp.route('/explorer')
@main_bp.route('/explorer/<int:folder_id>')
@login_required
def index(folder_id=None):

    current_folder = None
    if folder_id:
        current_folder = Folder.query.get_or_404(folder_id)
        # Access control
        if not current_user.is_admin:
            from models import Enrollment, FolderPermission
            enrolled = Enrollment.query.filter_by(user_id=current_user.id, folder_id=current_folder.id).first()
            granted = FolderPermission.query.filter_by(user_id=current_user.id, folder_id=current_folder.id).first()
            if not enrolled and not granted:
                flash('Access Denied: You do not have permission for this folder.', 'danger')
                return redirect(url_for('main.index'))
        
    # Search
    query = request.args.get('q')
    if query:
        files_query = File.query.filter(File.filename.ilike(f'%{query}%'))
        folders_query = Folder.query.filter(Folder.name.ilike(f'%{query}%'))
        
        if not current_user.is_admin:
            from models import Enrollment, FolderPermission
            enrolled_ids = [e.folder_id for e in Enrollment.query.filter_by(user_id=current_user.id).all()]
            granted_ids = [p.folder_id for p in FolderPermission.query.filter_by(user_id=current_user.id).all()]
            allowed_ids = set(enrolled_ids + granted_ids)
            folders_query = folders_query.filter(Folder.id.in_(allowed_ids))
            # Also filter files whose folders are restricted
            # (Simple check: if file is in a folder, check that folder's access)
            # This logic is a bit more complex for global search if we want to be 100% strict, 
            # but for now folders are the main entry point.
            
        files = files_query.all()
        folders = folders_query.all()
        breadcrumbs = [{'name': 'Search Results', 'url': '#'}]
    else:
        # Browse Folder
        folders_query = Folder.query.filter_by(parent_id=folder_id).order_by(Folder.name)
        if not current_user.is_admin:
            from models import Enrollment, FolderPermission
            enrolled_ids = [e.folder_id for e in Enrollment.query.filter_by(user_id=current_user.id).all()]
            granted_ids = [p.folder_id for p in FolderPermission.query.filter_by(user_id=current_user.id).all()]
            allowed_ids = set(enrolled_ids + granted_ids)
            folders_query = folders_query.filter(Folder.id.in_(allowed_ids))
            
        folders = folders_query.all()
        files = File.query.filter_by(folder_id=folder_id).order_by(File.filename).all()
        
        # Build breadcrumbs
        breadcrumbs = []
        travel = current_folder
        while travel:
            breadcrumbs.insert(0, {'name': travel.name, 'url': url_for('main.index', folder_id=travel.id)})
            travel = travel.parent if travel.parent_id else None
        breadcrumbs.insert(0, {'name': 'Home', 'url': url_for('main.index')})

    return render_template('main/dashboard.html', 
                         current_folder=current_folder, 
                         folders=folders, 
                         files=files,
                         breadcrumbs=breadcrumbs,
                         query=query,
                         completed_file_ids=[p.file_id for p in current_user.progress])

@main_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    folder_id = request.form.get('folder_id')
    folder_id = int(folder_id) if folder_id and folder_id != 'None' else None
    
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('main.index', folder_id=folder_id))
        
    uploaded_files = request.files.getlist('file')
    
    if not uploaded_files:
        flash('No selected file', 'danger')
        return redirect(url_for('main.index', folder_id=folder_id))

    count = 0
    for file in uploaded_files:
        if file.filename == '':
            continue
            
        filename = secure_filename(file.filename)
        # Unique filename implementation to prevent overwrites
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name)
        file.save(file_path)
        
        size = os.path.getsize(file_path)
        file_type = get_file_type(filename)
        
        new_file = File(
            filename=filename,
            path=unique_name,
            file_type=file_type,
            size=size,
            folder_id=folder_id,
            uploader_id=current_user.id
        )
        db.session.add(new_file)
        
        # Audit
        db.session.add(AuditLog(user_id=current_user.id, action='Upload', details=f'Uploaded {filename}'))
        count += 1
        
    db.session.commit()
    flash(f'{count} files uploaded.', 'success')
    return redirect(url_for('main.index', folder_id=folder_id))

@main_bp.route('/create_folder', methods=['POST'])
@login_required
def create_folder():
    name = request.form.get('name')
    parent_id = request.form.get('parent_id')
    is_training = request.form.get('is_training') == 'true'
    parent_id = int(parent_id) if parent_id and parent_id != 'None' else None
    
    if name:
        new_folder = Folder(name=name, parent_id=parent_id, is_training=is_training)
        db.session.add(new_folder)
        db.session.add(AuditLog(user_id=current_user.id, action='Create Folder', details=f'Created folder {name} (Training: {is_training})'))
        db.session.commit()
        flash('Folder created.', 'success')
        
    return redirect(url_for('main.index', folder_id=parent_id))

@main_bp.route('/file/<int:file_id>')
@login_required
def view_file(file_id):
    file = File.query.get_or_404(file_id)
    
    # Record progress if in training folder
    if file.folder and file.folder.is_training:
        from models import UserProgress
        existing = UserProgress.query.filter_by(user_id=current_user.id, file_id=file.id).first()
        if not existing:
            progress = UserProgress(user_id=current_user.id, file_id=file.id)
            db.session.add(progress)
            db.session.commit()
    
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], file.path, as_attachment=False)

@main_bp.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    file = File.query.get_or_404(file_id)
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], file.path, as_attachment=True, download_name=file.filename)

@main_bp.route('/rename', methods=['POST'])
@login_required
def rename_item():
    item_type = request.form.get('type') # 'file' or 'folder'
    item_id = request.form.get('id')
    new_name = request.form.get('name')
    
    parent_id = None
    
    if item_type == 'file':
        item = File.query.get_or_404(item_id)
        parent_id = item.folder_id
        old_name = item.filename
        item.filename = new_name # Should sanitize? secure_filename might strip spaces user wants. Let's allow simple text.
    else:
        item = Folder.query.get_or_404(item_id)
        parent_id = item.parent_id
        old_name = item.name
        item.name = new_name
        
    db.session.add(AuditLog(user_id=current_user.id, action='Rename', details=f'Renamed {item_type} {old_name} to {new_name}'))
    db.session.commit()
    flash('Renamed successfully.', 'success')
    
    return redirect(url_for('main.index', folder_id=parent_id))

@main_bp.route('/delete', methods=['POST'])
@login_required
def delete_item():
    item_type = request.form.get('type')
    item_id = request.form.get('id')
    
    parent_id = None
    
    if item_type == 'file':
        item = File.query.get_or_404(item_id)
        parent_id = item.folder_id
        # Delete from disk
        try:
            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], item.path))
        except OSError:
            pass # File might not exist
        db.session.delete(item)
    else:
        item = Folder.query.get_or_404(item_id)
        parent_id = item.parent_id
        # Recursive delete? Or block if not empty?
        # Recursive delete implementation
        def delete_folder_recursively(folder):
            # Delete subfolders
            for subfolder in folder.subfolders:
                delete_folder_recursively(subfolder)
            
            # Delete files in this folder
            for file in folder.files:
                try:
                    os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], file.path))
                except OSError:
                    pass
                db.session.delete(file)
            
            # Delete the folder itself
            db.session.delete(folder)

        delete_folder_recursively(item)
        
    db.session.add(AuditLog(user_id=current_user.id, action='Delete', details=f'Deleted {item_type} {item_id}'))
    db.session.commit()
    flash('Deleted successfully.', 'success')
    
    return redirect(url_for('main.index', folder_id=parent_id))
