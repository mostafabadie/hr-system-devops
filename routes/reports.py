"""Routes for reports and API endpoints."""
from flask import Blueprint, redirect, render_template, jsonify, request, url_for, session, flash
from datetime import date, datetime, timedelta
from db import get_db_connection
from reporting_functions import (
    get_daily_attendance_summary, get_attendance_overview_by_date,
    get_employee_attendance_trend, get_total_payroll_by_month,
    get_leave_usage_by_type, get_annual_leave_summary
)

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    today = date.today().strftime("%Y-%m-%d")
    current_month = date.today().strftime("%Y-%m")
    current_year = date.today().year

    # KPI Cards
    total_employees = conn.execute('SELECT COUNT(*) as count FROM employees').fetchone()['count']
    total_departments = conn.execute('SELECT COUNT(DISTINCT department) as count FROM employees').fetchone()['count']

    # Attendance today
    present_today = conn.execute(
        "SELECT COUNT(DISTINCT employee_id) as count FROM attendance WHERE date = ? AND check_in IS NOT NULL",
        (today,)
    ).fetchone()['count']

    all_employee_ids = [row[0] for row in conn.execute('SELECT id FROM employees').fetchall()]
    present_employee_ids = [row[0] for row in conn.execute(
        "SELECT DISTINCT employee_id FROM attendance WHERE date = ? AND check_in IS NOT NULL", (today,)
    ).fetchall()]
    absent_today = len(set(all_employee_ids) - set(present_employee_ids))

    on_leave_today = conn.execute('''
        SELECT COUNT(DISTINCT employee_id) as count FROM leave_requests
        WHERE ? BETWEEN start_date AND end_date AND status = 'approved'
    ''', (today,)).fetchone()['count']

    pending_leaves = conn.execute(
        "SELECT COUNT(*) as count FROM leave_requests WHERE status = 'pending'"
    ).fetchone()['count']

    avg_performance = conn.execute('''
        SELECT AVG(CAST(overall_score AS FLOAT)) as avg_score
        FROM performance_evaluations
        WHERE overall_score IS NOT NULL
    ''').fetchone()['avg_score'] or 0

    monthly_payroll = conn.execute('''
        SELECT SUM(net_salary) as total FROM payrolls
        WHERE substr(payment_date, 1, 7) = ?
    ''', (current_month,)).fetchone()['total'] or 0

    # Chart Data
    department_data = conn.execute(
        'SELECT department, COUNT(*) as count FROM employees GROUP BY department'
    ).fetchall()

    thirty_days_ago = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
    attendance_trend = conn.execute('''
        SELECT date,
               COUNT(CASE WHEN check_in IS NOT NULL THEN 1 END) as present,
               COUNT(DISTINCT employee_id) as total_employees
        FROM attendance
        WHERE date >= ?
        GROUP BY date
        ORDER BY date
    ''', (thirty_days_ago,)).fetchall()

    leave_usage = conn.execute('''
        SELECT lt.name as leave_type, SUM(lr.days_requested) as total_days
        FROM leave_requests lr
        JOIN leave_types lt ON lr.leave_type_id = lt.id
        WHERE lr.status = 'approved' AND strftime('%Y', lr.start_date) = ?
        GROUP BY lt.name
        ORDER BY total_days DESC
    ''', (str(current_year),)).fetchall()

    monthly_salaries = conn.execute('''
        SELECT substr(payment_date, 1, 7) as month, SUM(net_salary) as total
        FROM payrolls
        WHERE strftime('%Y', payment_date) = ?
        GROUP BY substr(payment_date, 1, 7)
        ORDER BY month
    ''', (str(current_year),)).fetchall()

    performance_dist = conn.execute('''
        SELECT overall_rating, COUNT(*) as count
        FROM performance_evaluations
        WHERE overall_rating IS NOT NULL
        GROUP BY overall_rating
        ORDER BY overall_rating
    ''').fetchall()

    dept_salary_avg = conn.execute('''
        SELECT department, AVG(salary) as avg_salary
        FROM employees
        WHERE salary > 0
        GROUP BY department
        ORDER BY avg_salary DESC
    ''').fetchall()

    dept_attendance = conn.execute('''
        SELECT e.department,
               COUNT(CASE WHEN a.check_in IS NOT NULL THEN 1 END) as present_count,
               COUNT(e.id) as total_employees,
               COUNT(a.id) as total_records
        FROM employees e
        LEFT JOIN attendance a ON e.id = a.employee_id AND substr(a.date, 1, 7) = ?
        GROUP BY e.department
        ORDER BY present_count DESC
    ''', (current_month,)).fetchall()

    # Tables
    top_absentees = conn.execute('''
        SELECT e.name, e.department,
               COUNT(CASE WHEN a.check_in IS NULL THEN 1 END) as absent_days
        FROM employees e
        LEFT JOIN attendance a ON e.id = a.employee_id AND a.date >= ?
        GROUP BY e.id
        HAVING absent_days > 0
        ORDER BY absent_days DESC
        LIMIT 5
    ''', (thirty_days_ago,)).fetchall()

    recent_leaves = conn.execute('''
        SELECT lr.id, e.name as employee_name, lt.name as leave_type,
               lr.start_date, lr.end_date, lr.status, lr.request_date
        FROM leave_requests lr
        JOIN employees e ON lr.employee_id = e.id
        JOIN leave_types lt ON lr.leave_type_id = lt.id
        ORDER BY lr.request_date DESC
        LIMIT 5
    ''').fetchall()

    pending_evaluations = conn.execute('''
        SELECT pe.id, e.name as employee_name, ep.name as period_name, pe.status
        FROM performance_evaluations pe
        JOIN employees e ON pe.employee_id = e.id
        JOIN evaluation_periods ep ON pe.period_id = ep.id
        WHERE pe.status = 'pending'
        LIMIT 5
    ''').fetchall()

    top_earners = conn.execute('''
        SELECT e.name, e.department, e.salary
        FROM employees e
        WHERE e.salary > 0
        ORDER BY e.salary DESC
        LIMIT 5
    ''').fetchall()

    conn.close()

    return render_template('dashboard.html',
                           total_employees=total_employees,
                           total_departments=total_departments,
                           present_today=present_today,
                           absent_today=absent_today,
                           on_leave_today=on_leave_today,
                           pending_leaves=pending_leaves,
                           avg_performance=round(avg_performance, 1) if avg_performance else 0,
                           monthly_payroll=monthly_payroll,
                           department_data=department_data,
                           attendance_trend=attendance_trend,
                           leave_usage=leave_usage,
                           monthly_salaries=monthly_salaries,
                           performance_dist=performance_dist,
                           dept_salary_avg=dept_salary_avg,
                           dept_attendance=dept_attendance,
                           top_absentees=top_absentees,
                           recent_leaves=recent_leaves,
                           pending_evaluations=pending_evaluations,
                           top_earners=top_earners,
                           current_month=current_month,
                           current_year=current_year,
                           current_date=today)


# Reports Pages
@reports_bp.route('/reports/leaves')
def leave_reports():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    current_year = datetime.now().year
    leave_summary = get_annual_leave_summary(current_year)
    leave_usage = get_leave_usage_by_type(current_year)
    return render_template('leave_reports.html',
                         leave_summary=leave_summary,
                         leave_usage=leave_usage,
                         year=current_year)


# API Endpoints
@reports_bp.route('/api/reports/attendance_overview')
def api_attendance_overview():
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    overview = get_attendance_overview_by_date(start_date, end_date)
    return jsonify([dict(row) for row in overview])


@reports_bp.route('/api/reports/payroll_monthly')
def api_payroll_monthly():
    year = request.args.get('year', datetime.now().year)
    total_payroll = get_total_payroll_by_month(year)
    return jsonify([dict(row) for row in total_payroll])


@reports_bp.route('/api/reports/leave_usage')
def api_leave_usage():
    year = request.args.get('year', datetime.now().year)
    usage = get_leave_usage_by_type(year)
    return jsonify([dict(row) for row in usage])


@reports_bp.route('/api/reports/employee_attendance/<int:employee_id>')
def api_employee_attendance_trend(employee_id):
    year = request.args.get('year', datetime.now().year)
    trend = get_employee_attendance_trend(employee_id, year)
    return jsonify([dict(row) for row in trend])
