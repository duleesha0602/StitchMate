import os
from datetime import datetime
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    """Check if uploaded file has a permitted extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file_storage, upload_folder):
    """Save an uploaded file safely and return the generated filename"""
    if file_storage and file_storage.filename != '' and allowed_file(file_storage.filename):
        ext = file_storage.filename.rsplit('.', 1)[1].lower()
        new_filename = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.{ext}"
        filepath = os.path.join(upload_folder, new_filename)
        file_storage.save(filepath)
        return new_filename
    return None
