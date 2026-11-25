from flask import Blueprint, request, redirect, session, url_for
from db import get_db_connection

language_bp = Blueprint('language', __name__)

@language_bp.route('/set-language/<lang>')
def set_language(lang):
    """Switch language between 'en' and 'si'"""
    if lang not in ['en', 'si']:
        lang = 'en'
    
    session['lang'] = lang

    # If user is logged in, persist to users table
    if 'user_id' in session:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE `users` SET `language` = %s WHERE `id` = %s", (lang, session['user_id']))
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    # Redirect back to referring page or index
    referrer = request.referrer
    if referrer:
        return redirect(referrer)
    return redirect(url_for('auth.index'))
