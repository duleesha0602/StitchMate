from datetime import date
from flask import Blueprint, render_template, redirect, url_for, session
from db import get_db_connection

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    """Tailor Dashboard: Banner Photo, Workroom metrics & recent orders (ss1.PNG, Req 2)"""
    if session.get('role') != 'tailor':
        return redirect(url_for('auth.index'))

    today_str = date.today().strftime('%Y-%m-%d')
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Total customers
            cursor.execute("SELECT COUNT(*) AS cnt FROM `customers`")
            total_customers = cursor.fetchone()['cnt']

            # Due Today
            cursor.execute("SELECT COUNT(*) AS cnt FROM `orders` WHERE `due_date` = %s AND `status` != 'Cancelled'", (today_str,))
            due_today = cursor.fetchone()['cnt']

            # Overdue
            cursor.execute("SELECT COUNT(*) AS cnt FROM `orders` WHERE `due_date` < %s AND `status` NOT IN ('Ready', 'Cancelled')", (today_str,))
            overdue = cursor.fetchone()['cnt']

            # Ready
            cursor.execute("SELECT COUNT(*) AS cnt FROM `orders` WHERE `status` = 'Ready'")
            ready = cursor.fetchone()['cnt']

            # Total Active Orders
            cursor.execute("SELECT COUNT(*) AS cnt FROM `orders` WHERE `status` NOT IN ('Ready', 'Cancelled')")
            total_active_orders = cursor.fetchone()['cnt']

            # Recent Orders
            cursor.execute("""
                SELECT o.*, c.nickname, c.name AS customer_name
                FROM `orders` o
                JOIN `customers` c ON o.customer_id = c.id
                ORDER BY o.id DESC LIMIT 6
            """)
            recent_orders = cursor.fetchall()

            # Tailor profile
            cursor.execute("SELECT * FROM `tailor_profiles` WHERE `user_id` = %s", (session['user_id'],))
            tailor = cursor.fetchone()
    finally:
        conn.close()

    return render_template('dashboard.html',
                           active_page='dashboard',
                           total_customers=total_customers,
                           due_today=due_today,
                           overdue=overdue,
                           ready=ready,
                           total_active_orders=total_active_orders,
                           recent_orders=recent_orders,
                           tailor=tailor)
