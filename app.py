from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask import jsonify
from datetime import datetime, date, timedelta
from werkzeug.security import check_password_hash
import os
import config
import logging
from logging.handlers import RotatingFileHandler
from db import get_db_connection, init_db, ensure_employee_portal_columns, ensure_payroll_schema, ensure_indexes, ensure_evaluation_periods_status
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
csrf = CSRFProtect(app)

# Session settings
app.config['PERMANENT_SESSION_LIFETIME'] = config.PERMANENT_SESSION_LIFETIME
app.config['SESSION_TIMEOUT'] = config.SESSION_TIMEOUT

# Configure logging
if not app.debug:
    file_handler = RotatingFileHandler(
        os.path.join(BASE_DIR, 'data', 'app.log'),
        maxBytes=10240, backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.DEBUG)

app.logger.info('HR System startup')




# Initialize database on startup
init_db()
ensure_employee_portal_columns()
ensure_payroll_schema()
ensure_indexes()
ensure_evaluation_periods_status()

# Register Blueprints
from routes.employees import employees_bp
from routes.leaves import leaves_bp
from routes.performance import performance_bp
from routes.portal import portal_bp
from routes.reports import reports_bp
from api.v1 import api_bp
from api.webhooks import webhooks_bp
from admin.dashboard import admin_bp

app.register_blueprint(employees_bp)
app.register_blueprint(leaves_bp)
app.register_blueprint(performance_bp)
app.register_blueprint(portal_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(api_bp)
app.register_blueprint(webhooks_bp)
app.register_blueprint(admin_bp)

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Server error: {error}")
    return "Internal server error", 500

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == config.ADMIN_USERNAME and \
           check_password_hash(config.ADMIN_PASSWORD_HASH, password):
            app.logger.info(f"Successful login for user: {username}")
            session['logged_in'] = True
            session.permanent = True
            return redirect(url_for('index'))
        else:
            app.logger.warning(f"Failed login attempt for user: {username}")
            error = 'بيانات الدخول غير صحيحة'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    app.logger.info(f"User logged out: {session.get('employee_name', session.get('logged_in', 'unknown'))}")
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    total_employees = conn.execute("SELECT COUNT(*) AS c FROM employees").fetchone()["c"]
    today_str = date.today().strftime("%Y-%m-%d")
    present_today = conn.execute(
        "SELECT COUNT(DISTINCT employee_id) AS c FROM attendance WHERE date = ? AND check_in IS NOT NULL",
        (today_str,)
    ).fetchone()["c"]
    absent_today = max(total_employees - present_today, 0)
    on_leave_today = conn.execute(
        "SELECT COUNT(DISTINCT employee_id) as count FROM leave_requests WHERE ? BETWEEN start_date AND end_date AND status = 'approved'",
        (today_str,)
    ).fetchone()['count']
    if total_employees > 0:
        present_pct = round(present_today / total_employees * 100)
        absent_pct = round(absent_today / total_employees * 100)
        leave_pct = round(on_leave_today / total_employees * 100)
    else:
        present_pct = absent_pct = leave_pct = 0
    conn.close()
    return render_template(
        'index.html',
        total_employees_home=total_employees,
        today_date_home=today_str,
        present_today_home=present_today,
        absent_today_home=absent_today,
        on_leave_today_home=on_leave_today,
        present_pct=present_pct,
        absent_pct=absent_pct,
        leave_pct=leave_pct,
    )

@app.template_filter('format_date')
def format_date(value):
    if value:
        try:
            if isinstance(value, datetime):
                return value.strftime("%Y-%m-%d")
            return str(value).split(" ")[0]
        except:
            return value
    return "-"

@app.template_filter('number_format')
def number_format_filter(value):
    try:
        return "{:,.0f}".format(float(value))
    except:
        return value

@app.template_filter('format_time')
def format_time(value):
    if value:
        try:
            if isinstance(value, datetime):
                return value.strftime("%H:%M")
            parts = str(value).split(" ")
            if len(parts) > 1:
                return parts[1]
        except:
            pass
    return "-"

@app.template_filter('to_date')
def to_date(value):
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            try:
                return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
    return value

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
