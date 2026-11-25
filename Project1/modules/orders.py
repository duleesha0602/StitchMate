import json
from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from db import get_db_connection
from utils import save_uploaded_file

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/orders')
def orders_list():
    """All Orders with Status Filter Pills (ss4.PNG, Req 4)"""
    if 'role' not in session:
        return redirect(url_for('auth.index'))

    status_filter = request.args.get('status', 'all').lower()
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = """
                SELECT o.*, c.nickname, c.name AS customer_name
                FROM `orders` o
                JOIN `customers` c ON o.customer_id = c.id
            """
            params = []

            # If customer logged in, restrict to own orders
            if session['role'] == 'customer':
                query += " WHERE o.customer_id = %s"
                params.append(session.get('customer_id'))
                if status_filter in ['pending', 'cutting', 'stitching', 'ready', 'cancelled']:
                    query += " AND LOWER(o.status) = %s"
                    params.append(status_filter)
            else:
                if status_filter in ['pending', 'cutting', 'stitching', 'ready', 'cancelled']:
                    query += " WHERE LOWER(o.status) = %s"
                    params.append(status_filter)

            query += " ORDER BY o.id DESC"
            cursor.execute(query, tuple(params))
            orders = cursor.fetchall()
    finally:
        conn.close()

    return render_template('orders.html', active_page='orders', orders=orders, current_status=status_filter)

@orders_bp.route('/orders/new', methods=['GET', 'POST'])
def order_new():
    """6-Section Order Creation Form (ss7.PNG)"""
    if session.get('role') != 'tailor':
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    try:
        if request.method == 'POST':
            customer_id = request.form.get('customer_id')
            clothing_type = request.form.get('clothing_type')
            other_clothing_name = request.form.get('other_clothing_name', '').strip() if clothing_type == 'Other' else None
            measurement_id = request.form.get('measurement_id') or None
            
            design_description = request.form.get('design_description', '').strip()
            fabric_type = request.form.get('fabric_type', '').strip()
            fabric_colour = request.form.get('fabric_colour', '').strip()
            fabric_description = request.form.get('fabric_description', '').strip()
            
            order_date_val = request.form.get('order_date') or date.today().strftime('%Y-%m-%d')
            due_date_val = request.form.get('due_date')
            total_price = float(request.form.get('total_price') or 0.0)

            advance_paid = 1 if request.form.get('advance_paid') == 'yes' else 0
            advance_amount = float(request.form.get('advance_amount') or 0.0) if advance_paid else 0.0
            
            # Validation: advance cannot exceed total price
            if advance_amount > total_price:
                advance_amount = total_price
            remaining_balance = max(0.0, total_price - advance_amount)

            # File uploads
            upload_folder = current_app.config['UPLOAD_FOLDER']
            design_photo = save_uploaded_file(request.files.get('design_photo'), upload_folder)
            fabric_photo = save_uploaded_file(request.files.get('fabric_photo'), upload_folder)

            with conn.cursor() as cursor:
                # Next order code (ORD001, ORD002, ...)
                cursor.execute("SELECT MAX(id) AS max_id FROM `orders`")
                max_id = cursor.fetchone()['max_id'] or 0
                order_code = f"ORD{max_id + 1:03d}"

                cursor.execute("""
                    INSERT INTO `orders` (
                        `order_code`, `customer_id`, `measurement_id`, `clothing_type`, `other_clothing_name`,
                        `design_description`, `design_photo`, `fabric_type`, `fabric_colour`, `fabric_description`, `fabric_photo`,
                        `order_date`, `due_date`, `total_price`, `advance_paid`, `advance_amount`, `remaining_balance`, `status`
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, 'Pending'
                    )
                """, (order_code, customer_id, measurement_id, clothing_type, other_clothing_name,
                      design_description, design_photo, fabric_type, fabric_colour, fabric_description, fabric_photo,
                      order_date_val, due_date_val, total_price, advance_paid, advance_amount, remaining_balance))
                order_id = cursor.lastrowid

                # Initial status history record
                cursor.execute("""
                    INSERT INTO `order_status_history` (`order_id`, `old_status`, `new_status`, `changed_by`, `note`)
                    VALUES (%s, 'New Order', 'Pending', 'Tailor', 'Order placed into atelier queue')
                """, (order_id,))
            conn.commit()

            flash(f"Commission order {order_code} registered successfully!", 'success')
            return redirect(url_for('orders.orders_list'))

        # GET request
        selected_cust_id = request.args.get('customer_id', type=int)
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, customer_code, name, nickname, primary_contact FROM `customers` ORDER BY `name` ASC")
            customers = cursor.fetchall()

            # Load all measurements for client-side selection
            cursor.execute("SELECT id, customer_id, measurement_code, measurement_date, unit FROM `measurements` ORDER BY id DESC")
            measurements = cursor.fetchall()
            
            for m in measurements:
                if isinstance(m['measurement_date'], (date, datetime)):
                    m['measurement_date'] = m['measurement_date'].strftime('%Y-%m-%d')
            measurements_json = json.dumps(measurements)
    finally:
        conn.close()

    return render_template('order_new.html',
                           active_page='orders',
                           customers=customers,
                           measurements_json=measurements_json,
                           selected_customer_id=selected_cust_id,
                           today_date=date.today().strftime('%Y-%m-%d'))

@orders_bp.route('/orders/<int:order_id>')
def order_detail(order_id):
    """Order Details, Associated Measurement, Design/Fabric & Audit Log"""
    if 'role' not in session:
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT o.*, c.name AS customer_name, c.nickname, c.customer_code, c.primary_contact
                FROM `orders` o
                JOIN `customers` c ON o.customer_id = c.id
                WHERE o.id = %s
            """, (order_id,))
            order = cursor.fetchone()

            if not order:
                flash('Order not found.', 'danger')
                return redirect(url_for('orders.orders_list'))

            # Ensure customer can only view own order
            if session['role'] == 'customer' and session.get('customer_id') != order['customer_id']:
                flash('Unauthorized access.', 'danger')
                return redirect(url_for('customer_portal.customer_portal'))

            # Associated measurement (if present)
            measurement = None
            if order['measurement_id']:
                cursor.execute("SELECT * FROM `measurements` WHERE `id` = %s", (order['measurement_id'],))
                measurement = cursor.fetchone()

            # Status history
            cursor.execute("""
                SELECT * FROM `order_status_history`
                WHERE `order_id` = %s
                ORDER BY `id` ASC
            """, (order_id,))
            status_history = cursor.fetchall()
    finally:
        conn.close()

    return render_template('order_detail.html',
                           active_page='orders',
                           order=order,
                           measurement=measurement,
                           status_history=status_history)

@orders_bp.route('/orders/<int:order_id>/update-status', methods=['POST'])
def order_update_status(order_id):
    """Update Order Status & Trigger Ready Notification to Customer"""
    if session.get('role') != 'tailor':
        return redirect(url_for('auth.index'))

    new_status = request.form.get('new_status')
    note = request.form.get('note', '').strip()

    if new_status not in ['Pending', 'Cutting', 'Stitching', 'Ready', 'Cancelled']:
        flash('Invalid status selection.', 'danger')
        return redirect(url_for('orders.order_detail', order_id=order_id))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM `orders` WHERE `id` = %s", (order_id,))
            order = cursor.fetchone()
            if not order:
                flash('Order not found.', 'danger')
                return redirect(url_for('orders.orders_list'))

            old_status = order['status']
            if old_status != new_status:
                cursor.execute("UPDATE `orders` SET `status` = %s WHERE `id` = %s", (new_status, order_id))

                cursor.execute("""
                    INSERT INTO `order_status_history` (`order_id`, `old_status`, `new_status`, `changed_by`, `note`)
                    VALUES (%s, %s, %s, 'Tailor', %s)
                """, (order_id, old_status, new_status, note or f'Progressed to {new_status}'))

                # Customer Notification: Only when order is Ready!
                if new_status == 'Ready':
                    cursor.execute("SELECT nickname FROM `customers` WHERE `id` = %s", (order['customer_id'],))
                    cust_nick = cursor.fetchone()['nickname']

                    title = f"Your order is ready! → {cust_nick}"
                    message = f"Your {order['clothing_type']} ({order['order_code']}) is now ready for collection."
                    
                    cursor.execute("""
                        INSERT INTO `notifications` (`customer_id`, `order_id`, `title`, `message`, `is_read`)
                        VALUES (%s, %s, %s, %s, 0)
                    """, (order['customer_id'], order_id, title, message))

        conn.commit()
        flash(f"Order status updated to {new_status}!", 'success')
    finally:
        conn.close()

    return redirect(url_for('orders.order_detail', order_id=order_id))

@orders_bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
def order_cancel(order_id):
    """Customer: Cancel Pending Order (Req 4)"""
    if 'role' not in session:
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM `orders` WHERE `id` = %s", (order_id,))
            order = cursor.fetchone()

            if not order:
                flash('Order not found.', 'danger')
                return redirect(url_for('orders.orders_list'))

            # If customer, verify ownership
            if session['role'] == 'customer' and order['customer_id'] != session.get('customer_id'):
                flash('Unauthorized to cancel this order.', 'danger')
                return redirect(url_for('customer_portal.customer_portal'))

            # Rule: Only Pending orders can be cancelled!
            if order['status'] != 'Pending':
                flash('Only orders in Pending status can be cancelled.', 'danger')
                return redirect(url_for('orders.order_detail', order_id=order_id))

            cursor.execute("UPDATE `orders` SET `status` = 'Cancelled' WHERE `id` = %s", (order_id,))

            actor = 'Customer' if session['role'] == 'customer' else 'Tailor'
            cursor.execute("""
                INSERT INTO `order_status_history` (`order_id`, `old_status`, `new_status`, `changed_by`, `note`)
                VALUES (%s, 'Pending', 'Cancelled', %s, 'Order cancelled by patron')
            """, (order_id, actor))

        conn.commit()
        flash('Order has been cancelled successfully.', 'info')
    finally:
        conn.close()

    if session['role'] == 'customer':
        return redirect(url_for('customer_portal.customer_portal'))
    return redirect(url_for('orders.order_detail', order_id=order_id))
