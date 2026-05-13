"""Routes for leave management."""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from db import get_db_connection
from leave_management import (
    submit_leave_request, approve_leave_request, reject_leave_request,
    get_employee_leave_requests, get_all_leave_requests, get_pending_leave_requests,
    get_employee_leave_balances, get_employee_leave_balance
)
from validators import validate_leave_dates

leaves_bp = Blueprint('leaves', __name__)


@leaves_bp.route('/leaves')
def leaves():
    """Page to view all leave requests for admins."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    requests = get_all_leave_requests()
    return render_template('leaves.html', requests=requests)


@leaves_bp.route('/leaves/pending')
def pending_leaves():
    """Page to view pending leave requests."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    requests = get_pending_leave_requests()
    return render_template('pending_leaves.html', requests=requests)


@leaves_bp.route('/leaves/request', methods=['GET', 'POST'])
def request_leave():
    """Leave request page for employees."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        employee_id = request.form['employee_id']
        leave_type_id = request.form['leave_type_id']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        reason = request.form['reason']

        is_valid, msg = validate_leave_dates(start_date, end_date)
        if not is_valid:
            flash(msg, 'error')
            return redirect(url_for('request_leave'))

        success, message = submit_leave_request(employee_id, leave_type_id, start_date, end_date, reason)

        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')

        return redirect(url_for('leaves.request_leave'))

    conn = get_db_connection()
    leave_types = conn.execute('SELECT id, name, max_days FROM leave_types').fetchall()
    conn.close()

    return render_template('request_leave.html', leave_types=leave_types)


@leaves_bp.route('/leaves/my_requests/<int:employee_id>')
def my_leave_requests(employee_id):
    """View leave requests for a specific employee."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    requests = get_employee_leave_requests(employee_id)
    balances = get_employee_leave_balances(employee_id)
    return render_template('my_leave_requests.html', requests=requests, balances=balances, employee_id=employee_id)


@leaves_bp.route('/leaves/approve/<int:request_id>', methods=['POST'])
def approve_leave(request_id):
    """Approve a leave request."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    approved_by = session.get('employee_id', 1)
    comments = request.form.get('comments', '')

    success, message = approve_leave_request(request_id, approved_by, comments)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')

    return redirect(url_for('leaves.pending_leaves'))


@leaves_bp.route('/leaves/reject/<int:request_id>', methods=['POST'])
def reject_leave(request_id):
    """Reject a leave request."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    approved_by = session.get('employee_id', 1)
    comments = request.form.get('comments', '')

    success, message = reject_leave_request(request_id, approved_by, comments)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')

    return redirect(url_for('pending_leaves'))


@leaves_bp.route('/leaves/balance/<int:employee_id>')
def leave_balance(employee_id):
    """View leave balance for an employee."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    create_leave_balance_for_employee(employee_id)

    balances = get_employee_leave_balances(employee_id)

    conn = get_db_connection()
    employee = conn.execute('SELECT name FROM employees WHERE id = ?', (employee_id,)).fetchone()
    conn.close()

    return render_template('leave_balance.html', balances=balances, employee=employee)


@leaves_bp.route('/api/leave_balance/<int:employee_id>/<int:leave_type_id>')
def api_leave_balance(employee_id, leave_type_id):
    """API to get leave balance."""
    balance = get_employee_leave_balance(employee_id, leave_type_id)

    if balance:
        return jsonify({
            'remaining_days': balance['remaining_days'],
            'used_days': balance['used_days'],
            'allocated_days': balance['allocated_days']
        })
    else:
        return jsonify({'error': 'Leave balance not found'}), 404
