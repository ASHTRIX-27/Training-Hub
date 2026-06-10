import os
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar'}

def get_file_type(filename):
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if ext in ['png', 'jpg', 'jpeg', 'gif']:
        return 'image'
    elif ext in ['mp4', 'mov', 'avi', 'mkv', 'webm']:
        return 'video'
    elif ext in ['pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx']:
        return 'document'
    return 'other'

def get_folder_path(folder_id):
    # This could be used if we wanted physical folders on disk matching DB folders.
    # For now, we will store all files in one flat 'uploads' dir or by date, and DB manages hierarchy.
    # User requested recursive folders. DB hierarchy is best for "virtual" folders, keeping storage flat or year/month.
    # Let's check the request: "user must be allowed to create folders with sub folders" -> Visual hierarchy.
    # Storing physically is harder to rename. Better to keep flat storage with unique names or IDs.
    pass
    
def human_readable_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"
