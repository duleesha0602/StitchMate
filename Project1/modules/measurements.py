from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_db_connection

measurements_bp = Blueprint('measurements', __name__)

@measurements_bp.route('/measurements')
def measurements_list():
    """Digital Measurement Locker (ss3.PNG, Req 7 & 11)"""
    if 'role' not in session:
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            if session['role'] == 'tailor':
                cursor.execute("""
                    SELECT m.*, c.name, c.nickname, c.customer_code
                    FROM `measurements` m
                    JOIN `customers` c ON m.customer_id = c.id
                    ORDER BY m.id DESC
                """)
            else:
                cursor.execute("""
                    SELECT m.*, c.name, c.nickname, c.customer_code
                    FROM `measurements` m
                    JOIN `customers` c ON m.customer_id = c.id
                    WHERE m.customer_id = %s
                    ORDER BY m.id DESC
                """, (session.get('customer_id'),))
            measurements = cursor.fetchall()

            # Custom types
            cursor.execute("SELECT * FROM `custom_measurement_types` ORDER BY id ASC")
            custom_types = cursor.fetchall()
    finally:
        conn.close()

    return render_template('measurements.html', 
                           active_page='measurements', 
                           measurements=measurements,
                           custom_types=custom_types)

@measurements_bp.route('/measurements/add', methods=['GET', 'POST'])
def measurement_add():
    """Add Measurement: Checks at least one value & preserves old records (ss8.PNG)"""
    if session.get('role') != 'tailor':
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    try:
        if request.method == 'POST':
            customer_id = request.form.get('customer_id')
            measurement_date = request.form.get('measurement_date') or date.today().strftime('%Y-%m-%d')
            unit = request.form.get('unit', 'Inches')

            # Helper to parse positive numeric values
            def parse_val(name):
                val = request.form.get(name, '').strip()
                try:
                    num = float(val)
                    return num if num > 0 else None
                except (ValueError, TypeError):
                    return None

            chest = parse_val('chest')
            waist = parse_val('waist')
            hip = parse_val('hip')
            shoulder = parse_val('shoulder')
            sleeve_length = parse_val('sleeve_length')
            dress_length = parse_val('dress_length')
            neck = parse_val('neck')
            arm_length = parse_val('arm_length')
            trouser_length = parse_val('trouser_length')
            inseam = parse_val('inseam')
            notes = request.form.get('notes', '').strip()

            # Mandatory condition: at least one measurement value must be entered
            if not any([chest, waist, hip, shoulder, sleeve_length, dress_length, neck, arm_length, trouser_length, inseam]):
                flash('Condition: You must provide at least one measurement value (Chest, Waist, Hip, Shoulder, etc.)!', 'danger')
                return redirect(url_for('measurements.measurement_add'))

            with conn.cursor() as cursor:
                cursor.execute("SELECT MAX(id) AS max_id FROM `measurements`")
                max_id = cursor.fetchone()['max_id'] or 0
                measurement_code = f"MEA{max_id + 1:03d}"

                cursor.execute("""
                    INSERT INTO `measurements` (
                        `measurement_code`, `customer_id`, `measurement_date`, `unit`,
                        `chest`, `waist`, `hip`, `shoulder`, `sleeve_length`, `dress_length`, `neck`,
                        `arm_length`, `trouser_length`, `inseam`, `notes`
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (measurement_code, customer_id, measurement_date, unit,
                      chest, waist, hip, shoulder, sleeve_length, dress_length, neck,
                      arm_length, trouser_length, inseam, notes))
            conn.commit()

            flash(f"Measurement record {measurement_code} saved permanently without overwriting old history!", 'success')
            return redirect(url_for('measurements.measurements_list'))

        # GET request
        selected_cust_id = request.args.get('customer_id', type=int)
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, customer_code, name, nickname FROM `customers` ORDER BY `name` ASC")
            customers = cursor.fetchall()
            
            cursor.execute("SELECT * FROM `custom_measurement_types` ORDER BY id ASC")
            custom_types = cursor.fetchall()
    finally:
        conn.close()

    return render_template('measurement_add.html',
                           active_page='measurements',
                           customers=customers,
                           custom_types=custom_types,
                           selected_customer_id=selected_cust_id,
                           today_date=date.today().strftime('%Y-%m-%d'))

@measurements_bp.route('/measurements/<int:measurement_id>/delete', methods=['POST'])
def measurement_delete(measurement_id):
    """Delete Saved Measurement (Req 4: Customer / Tailor)"""
    if 'role' not in session:
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM `measurements` WHERE `id` = %s", (measurement_id,))
            meas = cursor.fetchone()
            if not meas:
                flash('Measurement not found.', 'danger')
                return redirect(url_for('measurements.measurements_list'))

            # If customer, ensure it belongs to them
            if session['role'] == 'customer' and meas['customer_id'] != session.get('customer_id'):
                flash('Unauthorized to delete this measurement.', 'danger')
                return redirect(url_for('customer_portal.customer_portal'))

            cursor.execute("DELETE FROM `measurements` WHERE `id` = %s", (measurement_id,))
        conn.commit()
        flash('Measurement record deleted successfully.', 'success')
    finally:
        conn.close()

    if session['role'] == 'customer':
        return redirect(url_for('customer_portal.customer_portal'))
    return redirect(url_for('measurements.measurements_list'))

@measurements_bp.route('/custom-measurements', methods=['GET', 'POST'])
def custom_types():
    """Tailor: Add New Measurement Type Management (Req 13)"""
    if session.get('role') != 'tailor':
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM `tailor_profiles` WHERE `user_id` = %s", (session['user_id'],))
            tailor_p = cursor.fetchone()
            tailor_id = tailor_p['id'] if tailor_p else 1

            if request.method == 'POST':
                name = request.form.get('name', '').strip()
                unit = request.form.get('unit', 'Inches')
                description = request.form.get('description', '').strip()

                if name:
                    cursor.execute("""
                        INSERT INTO `custom_measurement_types` (`tailor_id`, `name`, `unit`, `description`)
                        VALUES (%s, %s, %s, %s)
                    """, (tailor_id, name, unit, description))
                    conn.commit()
                    flash(f"Custom measurement type '{name}' added successfully!", 'success')
                return redirect(url_for('measurements.custom_types'))

            cursor.execute("SELECT * FROM `custom_measurement_types` WHERE `tailor_id` = %s ORDER BY id DESC", (tailor_id,))
            types = cursor.fetchall()
    finally:
        conn.close()

    return render_template('custom_types.html', active_page='measurements', types=types)

@measurements_bp.route('/custom-measurements/<int:type_id>/delete', methods=['POST'])
def custom_type_delete(type_id):
    """Delete a custom measurement type (Req 13)"""
    if session.get('role') != 'tailor':
        return redirect(url_for('auth.index'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM `custom_measurement_types` WHERE `id` = %s", (type_id,))
        conn.commit()
        flash('Custom measurement type removed.', 'info')
    finally:
        conn.close()

    return redirect(url_for('measurements.custom_types'))
