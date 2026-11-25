from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.security import generate_password_hash
from db import get_db_connection
from utils import save_uploaded_file

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('/customers')
def customers_list():
    """Customer List with Instant Search & Direct Call (ss2.PNG, Req 3)"""
    if session.get('role') != 'tailor':
        return redirect(url_for('auth.index'))

    q = request.args.get('q', '').strip()
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            if q:
                search_term = f"%{q}%"
                cursor.execute("""
                    SELECT * FROM `customers`
                    WHERE `customer_code` LIKE %s OR `name` LIKE %s OR `nickname` LIKE %s OR `primary_contact` LIKE %s
                    ORDER BY `id` DESC
                """, (search_term, search_term, search_term, search_term))
            else:
                cursor.execute("SELECT * FROM `customers` ORDER BY `id` DESC")
            customers = cursor.fetchall()
    finally:
        conn.close()

    return render_template('customers.html', active_page='customers', customers=customers, search_query=q)

@customers_bp.route('/customers/add', methods=['GET', 'POST'])
def customer_add():
    """Customer Registration (Supports Walk-in and Online Patrons)"""
    if session.get('role') != 'tailor':
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    try:
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            nickname = request.form.get('nickname', '').strip()
            gender = request.form.get('gender', 'Female')
            primary_contact = request.form.get('primary_contact', '').strip()
            additional_contact = request.form.get('additional_contact', '').strip()
            address = request.form.get('address', '').strip()
            create_login = request.form.get('create_login', 'no')
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()

            photo_file = request.files.get('photo')
            photo_filename = save_uploaded_file(photo_file, current_app.config['UPLOAD_FOLDER'])

            with conn.cursor() as cursor:
                # Generate next customer code (CUS001, CUS002, ...)
                cursor.execute("SELECT MAX(id) AS max_id FROM `customers`")
                max_id = cursor.fetchone()['max_id'] or 0
                customer_code = f"CUS{max_id + 1:03d}"

                user_id = None
                login_status = 'Walk-in'

                # If Online Customer Account is requested
                if create_login == 'yes' and username and password:
                    pwd_hash = generate_password_hash(password)
                    cursor.execute("""
                        INSERT INTO `users` (`username`, `password`, `role`)
                        VALUES (%s, %s, 'customer')
                    """, (username, pwd_hash))
                    user_id = cursor.lastrowid
                    login_status = 'Online'

                cursor.execute("""
                    INSERT INTO `customers` (`customer_code`, `user_id`, `name`, `nickname`, `gender`, `primary_contact`, `address`, `photo`, `login_status`)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (customer_code, user_id, name, nickname, gender, primary_contact, address, photo_filename, login_status))
                customer_id = cursor.lastrowid

                # Record primary contact in contact numbers table
                cursor.execute("""
                    INSERT INTO `customer_contact_numbers` (`customer_id`, `phone_number`, `type`, `is_primary`)
                    VALUES (%s, %s, 'Current', 1)
                """, (customer_id, primary_contact))

                # If additional contact was given, record it too
                if additional_contact:
                    cursor.execute("""
                        INSERT INTO `customer_contact_numbers` (`customer_id`, `phone_number`, `type`, `is_primary`)
                        VALUES (%s, %s, 'Current', 0)
                    """, (customer_id, additional_contact))

            conn.commit()
            flash(f"Customer {name} ({customer_code}) registered successfully!", 'success')
            return redirect(url_for('customers.customers_list'))

        # GET request: preview next code
        with conn.cursor() as cursor:
            cursor.execute("SELECT MAX(id) AS max_id FROM `customers`")
            max_id = cursor.fetchone()['max_id'] or 0
            next_code = f"CUS{max_id + 1:03d}"
    finally:
        conn.close()

    return render_template('customer_add.html', active_page='customers', next_code=next_code)

@customers_bp.route('/customers/<int:customer_id>')
def customer_profile(customer_id):
    """Customer Profile with Full Contact Preservation & Historical Timeline"""
    if 'role' not in session:
        return redirect(url_for('auth.index'))

    # If customer is logged in, ensure they can only view their own profile
    if session['role'] == 'customer' and session.get('customer_id') != customer_id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('customer_portal.customer_portal'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM `customers` WHERE `id` = %s", (customer_id,))
            customer = cursor.fetchone()
            if not customer:
                flash('Customer not found.', 'danger')
                return redirect(url_for('customers.customers_list'))

            # Contact numbers history
            cursor.execute("""
                SELECT * FROM `customer_contact_numbers`
                WHERE `customer_id` = %s
                ORDER BY `is_primary` DESC, `id` DESC
            """, (customer_id,))
            contact_history = cursor.fetchall()

            # Customer orders
            cursor.execute("""
                SELECT * FROM `orders`
                WHERE `customer_id` = %s
                ORDER BY `id` DESC
            """, (customer_id,))
            customer_orders = cursor.fetchall()
    finally:
        conn.close()

    return render_template('customer_profile.html',
                           active_page='customers',
                           customer=customer,
                           contact_history=contact_history,
                           customer_orders=customer_orders)

@customers_bp.route('/customers/<int:customer_id>/update-phone', methods=['POST'])
def customer_update_phone(customer_id):
    """Update Contact Number (Req 9)"""
    new_phone = request.form.get('new_phone', '').strip()
    if not new_phone:
        flash('Please provide a valid phone number.', 'danger')
        return redirect(url_for('customers.customer_profile', customer_id=customer_id))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Update customer primary contact
            cursor.execute("UPDATE `customers` SET `primary_contact` = %s WHERE `id` = %s", (new_phone, customer_id))

            # Update contact numbers
            cursor.execute("UPDATE `customer_contact_numbers` SET `phone_number` = %s WHERE `customer_id` = %s AND `is_primary` = 1", (new_phone, customer_id))

        conn.commit()
        flash('Phone number updated successfully!', 'success')
    finally:
        conn.close()

    if session.get('role') == 'customer':
        return redirect(url_for('customer_portal.customer_portal'))
    return redirect(url_for('customers.customer_profile', customer_id=customer_id))

@customers_bp.route('/customers/<int:customer_id>/create-account', methods=['POST'])
def customer_create_account(customer_id):
    """Convert a Walk-in Customer into an Online Customer (FR45)"""
    if session.get('role') != 'tailor':
        return redirect(url_for('auth.index'))

    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if not username or not password:
        flash('Username and password are required to create an online account.', 'danger')
        return redirect(url_for('customers.customer_profile', customer_id=customer_id))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            pwd_hash = generate_password_hash(password)
            cursor.execute("INSERT INTO `users` (`username`, `password`, `role`) VALUES (%s, %s, 'customer')", (username, pwd_hash))
            user_id = cursor.lastrowid

            cursor.execute("""
                UPDATE `customers`
                SET `user_id` = %s, `login_status` = 'Online'
                WHERE `id` = %s
            """, (user_id, customer_id))

        conn.commit()
        flash('Online login account created! The patron is now an Online Customer.', 'success')
    finally:
        conn.close()

    return redirect(url_for('customers.customer_profile', customer_id=customer_id))

@customers_bp.route('/customers/<int:customer_id>/delete', methods=['POST'])
def customer_delete(customer_id):
    """Delete Customer Function with Cascading Cleanup (Req 3)"""
    if session.get('role') != 'tailor':
        flash('Only tailor is authorized to delete customer records.', 'danger')
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_id, name, customer_code FROM `customers` WHERE `id` = %s", (customer_id,))
            cust = cursor.fetchone()
            if not cust:
                flash('Customer not found.', 'danger')
                return redirect(url_for('customers.customers_list'))

            user_id = cust['user_id']
            cust_name = cust['name']

            # Delete customer record (MySQL cascading will clean orders, measurements, contact numbers, notifications)
            cursor.execute("DELETE FROM `customers` WHERE `id` = %s", (customer_id,))

            # Also delete login user account if exists
            if user_id:
                cursor.execute("DELETE FROM `users` WHERE `id` = %s", (user_id,))

        conn.commit()
        flash(f"Customer {cust_name} and all associated records deleted permanently.", 'success')
    finally:
        conn.close()

    return redirect(url_for('customers.customers_list'))
