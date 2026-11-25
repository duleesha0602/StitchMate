from flask import Blueprint, render_template, redirect, url_for, session
from db import get_db_connection

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/notifications')
def notifications_view():
    """Customer Ready Notifications (ss6.PNG)"""
    if 'role' not in session:
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            if session['role'] == 'tailor':
                cursor.execute("SELECT * FROM `notifications` ORDER BY `id` DESC")
            else:
                cursor.execute("""
                    SELECT * FROM `notifications`
                    WHERE `customer_id` = %s
                    ORDER BY `id` DESC
                """, (session.get('customer_id'),))
            notifications = cursor.fetchall()
    finally:
        conn.close()

    return render_template('notifications.html', active_page='notifications', notifications=notifications)

@notifications_bp.route('/notifications/<int:notif_id>/mark-read', methods=['POST'])
def notification_mark_read(notif_id):
    """Mark a notification as read"""
    if 'role' not in session:
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE `notifications` SET `is_read` = 1 WHERE `id` = %s", (notif_id,))
        conn.commit()
    finally:
        conn.close()

    return redirect(url_for('notifications.notifications_view'))
