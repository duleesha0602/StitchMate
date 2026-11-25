from datetime import date
from flask import Blueprint, render_template, redirect, url_for, session
from db import get_db_connection

schedule_bp = Blueprint('schedule', __name__)

@schedule_bp.route('/work-schedule')
def work_schedule():
    """Work Schedule: Dynamic Calculation of Overdue, Due Today, Upcoming, Ready (ss5.PNG)"""
    if session.get('role') != 'tailor':
        return redirect(url_for('auth.index'))

    today_str = date.today().strftime('%Y-%m-%d')
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Overdue: due_date < today AND status != 'Ready'
            cursor.execute("""
                SELECT o.*, c.nickname
                FROM `orders` o
                JOIN `customers` c ON o.customer_id = c.id
                WHERE o.due_date < %s AND o.status != 'Ready'
                ORDER BY o.due_date ASC
            """, (today_str,))
            overdue_orders = cursor.fetchall()

            # Due Today: due_date == today
            cursor.execute("""
                SELECT o.*, c.nickname
                FROM `orders` o
                JOIN `customers` c ON o.customer_id = c.id
                WHERE o.due_date = %s
                ORDER BY o.id ASC
            """, (today_str,))
            due_today_orders = cursor.fetchall()

            # Upcoming: due_date > today
            cursor.execute("""
                SELECT o.*, c.nickname
                FROM `orders` o
                JOIN `customers` c ON o.customer_id = c.id
                WHERE o.due_date > %s
                ORDER BY o.due_date ASC
            """, (today_str,))
            upcoming_orders = cursor.fetchall()

            # Ready: status == 'Ready'
            cursor.execute("""
                SELECT o.*, c.nickname
                FROM `orders` o
                JOIN `customers` c ON o.customer_id = c.id
                WHERE o.status = 'Ready'
                ORDER BY o.due_date DESC
            """, ())
            ready_orders = cursor.fetchall()
    finally:
        conn.close()

    return render_template('work_schedule.html',
                           active_page='work_schedule',
                           overdue_orders=overdue_orders,
                           due_today_orders=due_today_orders,
                           upcoming_orders=upcoming_orders,
                           ready_orders=ready_orders)
