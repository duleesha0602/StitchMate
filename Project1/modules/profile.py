from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from db import get_db_connection
from utils import save_uploaded_file

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/tailor/profile', methods=['GET', 'POST'])
def tailor_profile():
    """Tailor Profile Management: Edit Name, Shop Name, Address, Contact & Photo (Req 5)"""
    if session.get('role') != 'tailor':
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    try:
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            shop_name = request.form.get('shop_name', '').strip()
            email = request.form.get('email', '').strip()
            primary_contact = request.form.get('primary_contact', '').strip()
            address = request.form.get('address', '').strip()

            photo_file = request.files.get('photo')
            photo_filename = save_uploaded_file(photo_file, current_app.config['UPLOAD_FOLDER'])

            with conn.cursor() as cursor:
                if photo_filename:
                    cursor.execute("""
                        UPDATE `tailor_profiles`
                        SET `name` = %s, `shop_name` = %s, `email` = %s, `primary_contact` = %s, `address` = %s, `photo` = %s
                        WHERE `user_id` = %s
                    """, (name, shop_name, email, primary_contact, address, photo_filename, session['user_id']))
                else:
                    cursor.execute("""
                        UPDATE `tailor_profiles`
                        SET `name` = %s, `shop_name` = %s, `email` = %s, `primary_contact` = %s, `address` = %s
                        WHERE `user_id` = %s
                    """, (name, shop_name, email, primary_contact, address, session['user_id']))

                # Update email in users table if needed
                if email:
                    cursor.execute("UPDATE `users` SET `username` = %s WHERE `id` = %s", (email, session['user_id']))

            conn.commit()
            session['name'] = name
            flash('Atelier Profile updated successfully! Changes reflect immediately across customer views.', 'success')
            return redirect(url_for('profile.tailor_profile'))

        # GET request
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM `tailor_profiles` WHERE `user_id` = %s", (session['user_id'],))
            profile = cursor.fetchone()
    finally:
        conn.close()

    return render_template('tailor_profile.html', active_page='profile', profile=profile)
