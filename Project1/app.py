import os
from flask import Flask, session, request, url_for as flask_url_for

from db import get_db_connection, init_db
from translations import translate

# Import Modular Blueprints
from modules.auth import auth_bp
from modules.dashboard import dashboard_bp
from modules.customers import customers_bp
from modules.measurements import measurements_bp
from modules.orders import orders_bp
from modules.schedule import schedule_bp
from modules.notifications import notifications_bp
from modules.customer_portal import customer_portal_bp
from modules.profile import profile_bp
from modules.settings import settings_bp
from modules.language import language_bp

# Initialize Flask Application
app = Flask(__name__)
app.secret_key = 'stitchmate_atelier_super_secret_key_2026'

# Upload configuration
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Register Modular Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(customers_bp)
app.register_blueprint(measurements_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(schedule_bp)
app.register_blueprint(notifications_bp)
app.register_blueprint(customer_portal_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(language_bp)

# Blueprint Endpoint Mapping for seamless template compatibility
ENDPOINT_MAP = {
    'index': 'auth.index',
    'login': 'auth.login',
    'register_tailor': 'auth.register_tailor',
    'logout': 'auth.logout',
    'dashboard': 'dashboard.dashboard',
    'customers_list': 'customers.customers_list',
    'customer_add': 'customers.customer_add',
    'customer_profile': 'customers.customer_profile',
    'customer_update_phone': 'customers.customer_update_phone',
    'customer_create_account': 'customers.customer_create_account',
    'customer_delete': 'customers.customer_delete',
    'measurements_list': 'measurements.measurements_list',
    'measurement_add': 'measurements.measurement_add',
    'measurement_delete': 'measurements.measurement_delete',
    'custom_types': 'measurements.custom_types',
    'custom_type_delete': 'measurements.custom_type_delete',
    'orders_list': 'orders.orders_list',
    'order_new': 'orders.order_new',
    'order_detail': 'orders.order_detail',
    'order_update_status': 'orders.order_update_status',
    'order_cancel': 'orders.order_cancel',
    'work_schedule': 'schedule.work_schedule',
    'notifications_view': 'notifications.notifications_view',
    'notification_mark_read': 'notifications.notification_mark_read',
    'customer_portal': 'customer_portal.customer_portal',
    'tailor_profile': 'profile.tailor_profile',
    'settings': 'settings.settings',
    'update_username': 'settings.update_username',
    'update_password': 'settings.update_password',
    'set_language': 'language.set_language'
}

def smart_url_for(endpoint, **values):
    resolved = ENDPOINT_MAP.get(endpoint, endpoint)
    return flask_url_for(resolved, **values)

app.jinja_env.globals['url_for'] = smart_url_for

# Global translation filter & function
def t_filter(key):
    lang = session.get('lang', 'en')
    return translate(key, lang)

app.jinja_env.filters['t'] = t_filter
app.jinja_env.globals['t'] = t_filter

# Context processor for global badge counts & language in templates
@app.context_processor
def inject_global_data():
    lang = session.get('lang', 'en')
    unread_count = 0
    tailor_shop = "StitchMate Atelier"

    if 'role' in session:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                if session['role'] == 'tailor':
                    cursor.execute("SELECT COUNT(*) AS cnt FROM `notifications` WHERE `is_read` = 0")
                    unread_count = cursor.fetchone()['cnt']
                elif session['role'] == 'customer' and 'customer_id' in session:
                    cursor.execute("SELECT COUNT(*) AS cnt FROM `notifications` WHERE `customer_id` = %s AND `is_read` = 0", (session['customer_id'],))
                    unread_count = cursor.fetchone()['cnt']
                
                cursor.execute("SELECT shop_name FROM `tailor_profiles` ORDER BY id ASC LIMIT 1")
                tp = cursor.fetchone()
                if tp:
                    tailor_shop = tp['shop_name']
        except Exception:
            pass
        finally:
            conn.close()

    return {
        'unread_notif_count': unread_count,
        'current_lang': lang,
        'tailor_shop_name': tailor_shop
    }

if __name__ == '__main__':
    init_db()
    print(" * StitchMate Atelier System initialized")
    print(" * Modular Architecture: 11 Sub-modules Registered")
    print(" * Database active on MySQL / phpMyAdmin: stitchmate_db")
    print(" * Running on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
