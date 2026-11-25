from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings')
def settings():
    """Account Security & Credentials Settings (Req 14)"""
    if 'role' not in session:
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM `users` WHERE `id` = %s", (session['user_id'],))
            user = cursor.fetchone()
    finally:
        conn.close()

    return render_template('settings.html', active_page='settings', user=user)

@settings_bp.route('/settings/update-username', methods=['POST'])
def update_username():
    """Update login username (ensures uniqueness across accounts)"""
    if 'role' not in session:
        return redirect(url_for('auth.index'))

    new_username = request.form.get('username', '').strip()
    if not new_username:
        flash('Username cannot be empty.', 'danger')
        return redirect(url_for('settings.settings'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Check uniqueness
            cursor.execute("SELECT id FROM `users` WHERE `username` = %s AND `id` != %s", (new_username, session['user_id']))
            if cursor.fetchone():
                flash('This username is already taken by another account.', 'danger')
                return redirect(url_for('settings.settings'))

            cursor.execute("UPDATE `users` SET `username` = %s WHERE `id` = %s", (new_username, session['user_id']))
        conn.commit()
        session['username'] = new_username
        flash('Username updated successfully!', 'success')
    finally:
        conn.close()

    return redirect(url_for('settings.settings'))

@settings_bp.route('/settings/update-password', methods=['POST'])
def update_password():
    """Update login password with current password verification"""
    if 'role' not in session:
        return redirect(url_for('auth.index'))

    current_pwd = request.form.get('current_password', '').strip()
    new_pwd = request.form.get('new_password', '').strip()
    confirm_pwd = request.form.get('confirm_password', '').strip()

    if not current_pwd or not new_pwd or not confirm_pwd:
        flash('Please fill in all password fields.', 'danger')
        return redirect(url_for('settings.settings'))

    if new_pwd != confirm_pwd:
        flash('New password and confirmation do not match.', 'danger')
        return redirect(url_for('settings.settings'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT password FROM `users` WHERE `id` = %s", (session['user_id'],))
            user = cursor.fetchone()

            if not user or not (check_password_hash(user['password'], current_pwd) or user['password'] == current_pwd):
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('settings.settings'))

            hashed = generate_password_hash(new_pwd)
            cursor.execute("UPDATE `users` SET `password` = %s WHERE `id` = %s", (hashed, session['user_id']))
        conn.commit()
        flash('Password updated successfully! Please use your new password next time.', 'success')
    finally:
        conn.close()

    return redirect(url_for('settings.settings'))
