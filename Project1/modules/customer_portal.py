from flask import Blueprint, render_template, redirect, url_for, session
from db import get_db_connection

customer_portal_bp = Blueprint('customer_portal', __name__)

@customer_portal_bp.route('/my-account')
def customer_portal():
    """Online Customer Dashboard: Banner Photo, Measurement Locker, Order Tracker & Guide (Req 2, 4, 6, 7, 11)"""
    if session.get('role') != 'customer':
        return redirect(url_for('auth.index'))

    customer_id = session.get('customer_id')
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Customer details
            cursor.execute("SELECT * FROM `customers` WHERE `id` = %s", (customer_id,))
            customer = cursor.fetchone()

            # Atelier profile / Tailor contact (for Call My Tailor)
            cursor.execute("SELECT * FROM `tailor_profiles` ORDER BY `id` ASC LIMIT 1")
            tailor_profile = cursor.fetchone()

            # Customer orders
            cursor.execute("SELECT * FROM `orders` WHERE `customer_id` = %s ORDER BY `id` DESC", (customer_id,))
            customer_orders = cursor.fetchall()

            # Customer measurements
            cursor.execute("SELECT * FROM `measurements` WHERE `customer_id` = %s ORDER BY `id` DESC", (customer_id,))
            customer_measurements = cursor.fetchall()

            # Contact numbers history
            cursor.execute("""
                SELECT * FROM `customer_contact_numbers`
                WHERE `customer_id` = %s
                ORDER BY `is_primary` DESC, `id` DESC
            """, (customer_id,))
            contact_history = cursor.fetchall()

            # Custom measurement types
            cursor.execute("SELECT * FROM `custom_measurement_types` ORDER BY id ASC")
            custom_types = cursor.fetchall()
    finally:
        conn.close()

    return render_template('customer_portal.html',
                           active_page='portal',
                           customer=customer,
                           tailor_profile=tailor_profile,
                           customer_orders=customer_orders,
                           customer_measurements=customer_measurements,
                           contact_history=contact_history,
                           custom_types=custom_types)
