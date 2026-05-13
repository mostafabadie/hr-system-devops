"""Routes for employee self-service portal."""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, timedelta
from db import get_db_connection
from leave_management import (
    calculate_leave_days, get_employee_leave_balance, create_leave_balance_for_employee,
    submit_leave_request, get_employee_leave_requests, get_employee_leave_balances
)
from reporting_functions import get_employee_attendance_trend
from performance_management import (
    get_employee_evaluations, get_employee_performance_trend
)

portal_bp = Blueprint('portal', __name__)


@portal_bp.route('/employee/login', methods=['GET', 'POST'])
def employee_login():
    """Employee login for self-service portal."""
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        conn = get_db_connection()
        employee = conn.execute(
            "SELECT * FROM employees WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if employee and employee['password_hash']:
            from werkzeug.security import check_password_hash
            if check_password_hash(employee['password_hash'], password):
                session.clear()
                session['employee_logged_in'] = True
                session['employee_id'] = employee['id']
                session['employee_name'] = employee['name']
                from app import app
                app.logger.info(f"Employee login: {employee['name']} (id={employee['id']})")
                return redirect(url_for('portal.self_portal'))
        if employee and not employee['password_hash']:
            error = 'حسابك غير مفعّل للبوابة الذاتية. تواصل مع المسؤول لتعيين اسم مستخدم وكلمة مرور.'
        else:
            error = 'بيانات الدخول غير صحيحة'

    return render_template('employee_login.html', error=error)


@portal_bp.route('/employee/logout')
def employee_logout():
    """Employee logout from self-service portal."""
    from app import app
    app.logger.info(f"Employee logged out: {session.get('employee_name', 'unknown')}")
    session.pop('employee_logged_in', None)
    session.pop('employee_id', None)
    session.pop('employee_name', None)
    return redirect(url_for('portal.employee_login'))


@portal_bp.route('/self/portal')
def self_portal():
    """Employee self-service portal home."""
    if not session.get('employee_logged_in'):
        return redirect(url_for('portal.employee_login'))

    emp_id = session.get('employee_id')
    conn = get_db_connection()
    employee = conn.execute('SELECT * FROM employees WHERE id = ?', (emp_id,)).fetchone()
    conn.close()

    return render_template('self_portal.html', employee=employee)


@portal_bp.route('/self/leaves/request', methods=['GET', 'POST'])
def self_request_leave():
    """Employee leave request + balance display."""
    if not session.get('employee_logged_in'):
        return redirect(url_for('portal.employee_login'))

    employee_id = session.get('employee_id')

    if request.method == 'POST':
        leave_type_id = request.form['leave_type_id']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        reason = request.form['reason']

        from validators import validate_leave_dates
        is_valid, msg = validate_leave_dates(start_date, end_date)
        if not is_valid:
            flash(msg, 'error')
            return redirect(url_for('portal.self_request_leave'))

        success, message = submit_leave_request(employee_id, leave_type_id, start_date, end_date, reason)

        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')

        return redirect(url_for('portal.self_request_leave'))

    conn = get_db_connection()
    leave_types = conn.execute('SELECT id, name, max_days FROM leave_types').fetchall()
    conn.close()

    balances = get_employee_leave_balances(employee_id)

    return render_template(
        'self_request_leave.html',
        leave_types=leave_types,
        balances=balances,
    )


@portal_bp.route('/self/performance/history')
def self_performance_history():
    """Employee performance history."""
    if not session.get('employee_logged_in'):
        return redirect(url_for('portal.employee_login'))

    employee_id = session.get('employee_id')

    conn = get_db_connection()
    employee = conn.execute('SELECT * FROM employees WHERE id = ?', (employee_id,)).fetchone()
    conn.close()

    if not employee:
        flash('الموظف غير موجود', 'error')
        return redirect(url_for('portal.self_portal'))

    evaluations = get_employee_evaluations(employee_id)
    trend = get_employee_performance_trend(employee_id)

    return render_template(
        'employee_performance_history.html',
        employee=employee,
        evaluations=evaluations,
        trend=trend,
    )


@portal_bp.route('/self/payroll')
def self_payroll():
    """Employee payroll view."""
    if not session.get('employee_logged_in'):
        return redirect(url_for('portal.employee_login'))

    employee_id = session.get('employee_id')

    conn = get_db_connection()
    payrolls = conn.execute("""
        SELECT id, salary, bonus, deductions, net_salary, payment_date
        FROM payrolls
        WHERE employee_id = ?
        ORDER BY payment_date DESC
    """, (employee_id,)).fetchall()
    conn.close()

    return render_template('self_payroll.html', payrolls=payrolls)
