"""Routes for performance evaluation management."""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from db import get_db_connection
from performance_management import (
    get_evaluation_criteria, add_evaluation_criteria, get_evaluation_periods,
    get_active_evaluation_period, create_evaluation_period,
    get_evaluations_by_period, get_pending_evaluations, get_employees_without_evaluation,
    get_evaluation_by_id, create_performance_evaluation, update_performance_evaluation,
    complete_performance_evaluation, get_employee_evaluations, get_employee_performance_trend,
    get_evaluation_statistics, get_criteria_performance_analysis, get_employees_with_evaluations,
    rating_to_score, score_to_rating
)
from datetime import datetime

performance_bp = Blueprint('performance', __name__)


@performance_bp.route('/performance')
def performance_dashboard():
    """Performance management dashboard."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    active_period = get_active_evaluation_period()

    stats = {}
    if active_period:
        stats['pending_evaluations'] = len(get_pending_evaluations(active_period['id']))
        stats['employees_without_evaluation'] = len(get_employees_without_evaluation(active_period['id']))
        stats['completed_evaluations'] = (
            len(get_evaluations_by_period(active_period['id'])) - stats['pending_evaluations']
        )

    return render_template('performance_dashboard.html',
                         active_period=active_period,
                         stats=stats)


@performance_bp.route('/performance/periods')
def evaluation_periods():
    """Manage evaluation periods."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    periods = get_evaluation_periods()
    return render_template('evaluation_periods.html', periods=periods)


@performance_bp.route('/performance/periods/create', methods=['GET', 'POST'])
def create_period():
    """Create a new evaluation period."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        year = int(request.form['year'])
        quarter = int(request.form['quarter'])

        period_id = create_evaluation_period(name, start_date, end_date, year, quarter)
        # Set status to 'active' for the new period (set others to completed)
        conn = get_db_connection()
        conn.execute("UPDATE evaluation_periods SET status = 'completed' WHERE id != ?", (period_id,))
        conn.execute("UPDATE evaluation_periods SET status = 'active' WHERE id = ?", (period_id,))
        conn.commit()
        conn.close()
        flash('تم إنشاء الفترة التقييمية بنجاح', 'success')
        return redirect(url_for('performance.evaluation_periods'))

    return render_template('create_period.html')


@performance_bp.route('/performance/periods/<int:period_id>/status', methods=['POST'])
def change_period_status(period_id):
    """Change the status of an evaluation period."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    new_status = request.form.get('status', 'completed')

    conn = get_db_connection()
    if new_status == 'completed':
        conn.execute("UPDATE evaluation_periods SET status = 'completed' WHERE id = ?", (period_id,))
        flash('تم إكمال الفترة التقييمية بنجاح', 'success')
    elif new_status == 'active':
        conn.execute("UPDATE evaluation_periods SET status = 'completed' WHERE status != 'completed'")
        conn.execute("UPDATE evaluation_periods SET status = 'active' WHERE id = ?", (period_id,))
        flash('تم تفعيل الفترة التقييمية', 'success')
    else:
        conn.execute("UPDATE evaluation_periods SET status = ? WHERE id = ?", (new_status, period_id))
        flash('تم تحديث حالة الفترة التقييمية', 'success')
    conn.commit()
    conn.close()

    return redirect(url_for('performance.evaluation_periods'))


@performance_bp.route('/performance/evaluate')
def evaluation_list():
    """List of evaluations."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    period_id = request.args.get('period_id')
    search_query = request.args.get('search', '').strip()

    try:
        page = int(request.args.get('page', 1))
        if page < 1:
            page = 1
    except ValueError:
        page = 1

    try:
        per_page = int(request.args.get('page_size', 20))
        if per_page not in (10, 20, 25, 50, 100):
            per_page = 20
    except ValueError:
        per_page = 20

    active_period = get_active_evaluation_period()

    if not period_id and active_period:
        period_id = active_period['id']

    evaluations = []
    employees = []
    total_employees = 0
    total_employees_without_eval = 0
    pages = 1
    start_index = 0
    end_index = 0

    if period_id:
        evaluations = get_evaluations_by_period(period_id)
        conn = get_db_connection()
        params = [period_id]
        base_query = """
            SELECT
                e.id,
                e.name,
                e.department,
                e.position,
                pe.id AS evaluation_id,
                pe.status AS evaluation_status
            FROM employees e
            LEFT JOIN performance_evaluations pe
              ON pe.employee_id = e.id AND pe.period_id = ?
        """
        if search_query:
            base_query += " WHERE e.name LIKE ? OR COALESCE(e.department,'') LIKE ? "
            params.extend([f"%{search_query}%", f"%{search_query}%"])
        base_query += " ORDER BY e.name"

        all_employees = conn.execute(base_query, params).fetchall()
        conn.close()

        total_employees = len(all_employees)
        total_employees_without_eval = sum(1 for row in all_employees if row["evaluation_id"] is None)
        pages = (total_employees + per_page - 1) // per_page if total_employees else 1
        start = (page - 1) * per_page
        end = start + per_page
        employees = all_employees[start:end]
        if total_employees:
            start_index = start + 1
            end_index = min(end, total_employees)

    periods = get_evaluation_periods()

    return render_template('evaluation_list.html',
                         evaluations=evaluations,
                         employees=employees,
                         total_employees=total_employees,
                         total_employees_in_period=total_employees,
                         total_employees_without_eval=total_employees_without_eval,
                         page=page,
                         pages=pages,
                         periods=periods,
                         search_query=search_query,
                         total_results=total_employees,
                         start_index=start_index,
                         end_index=end_index,
                         selected_period_id=int(period_id) if period_id else None,
                         page_size=per_page)


@performance_bp.route('/performance/evaluate/<int:employee_id>')
def evaluate_employee(employee_id):
    """Evaluate an employee."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    period_id = request.args.get('period_id')
    if not period_id:
        active_period = get_active_evaluation_period()
        if active_period:
            period_id = active_period['id']
        else:
            flash('لا توجد فترة تقييمية نشطة', 'error')
            return redirect(url_for('performance.evaluation_list'))

    conn = get_db_connection()
    employee = conn.execute('SELECT * FROM employees WHERE id = ?', (employee_id,)).fetchone()
    period = conn.execute('SELECT * FROM evaluation_periods WHERE id = ?', (period_id,)).fetchone()
    conn.close()

    if not employee:
        flash('الموظف غير موجود', 'error')
        return redirect(url_for('performance.evaluation_list'))

    existing_evaluation = None
    conn = get_db_connection()
    existing = conn.execute("""
        SELECT * FROM performance_evaluations
        WHERE employee_id = ? AND period_id = ?
    """, (employee_id, period_id)).fetchone()
    conn.close()

    if existing:
        existing_evaluation = get_evaluation_by_id(existing['id'])

    criteria = get_evaluation_criteria()

    return render_template('evaluate_employee.html',
                         employee=employee,
                         period=period,
                         criteria=criteria,
                         existing_evaluation=existing_evaluation)


@performance_bp.route('/performance/evaluate/<int:employee_id>/submit', methods=['POST'])
def submit_evaluation(employee_id):
    """Submit employee evaluation."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    period_id = request.form['period_id']
    evaluator_id = 1

    evaluation_data = {
        'overall_rating': request.form.get('overall_rating', ''),
        'strengths': request.form.get('strengths', ''),
        'areas_for_improvement': request.form.get('areas_for_improvement', ''),
        'goals_next_period': request.form.get('goals_next_period', ''),
        'comments': request.form.get('comments', ''),
        'criteria_details': []
    }

    criteria = get_evaluation_criteria()
    total_score = 0.0
    total_weight = 0.0

    for criterion in criteria:
        rating = request.form.get(f'criteria_{criterion["id"]}_rating')
        comments = request.form.get(f'criteria_{criterion["id"]}_comments', '')

        if rating:
            evaluation_data['criteria_details'].append({
                'criteria_id': criterion['id'],
                'rating': rating,
                'comments': comments
            })
            score = rating_to_score(rating)
            weight = criterion['weight']
            total_score += score * weight
            total_weight += weight

    if total_weight > 0:
        overall_score = total_score / total_weight
        evaluation_data['overall_score'] = overall_score
        if not evaluation_data['overall_rating']:
            evaluation_data['overall_rating'] = score_to_rating(overall_score)

    try:
        conn = get_db_connection()
        existing = conn.execute("""
            SELECT id FROM performance_evaluations
            WHERE employee_id = ? AND period_id = ?
        """, (employee_id, period_id)).fetchone()
        conn.close()

        evaluation_id = None
        if existing:
            update_performance_evaluation(existing['id'], evaluator_id, evaluation_data)
            evaluation_id = existing['id']
            flash('تم تحديث التقييم بنجاح', 'success')
        else:
            evaluation_id = create_performance_evaluation(employee_id, period_id, evaluator_id, evaluation_data)
            flash('تم إنشاء التقييم بنجاح', 'success')

        if request.form.get('complete_evaluation'):
            complete_performance_evaluation(evaluation_id, evaluator_id)
            flash('تم إكمال التقييم', 'success')

    except Exception as e:
        from app import app
        app.logger.error(f"Evaluation error: {str(e)}")
        flash(f'حدث خطأ أثناء حفظ التقييم: {str(e)}', 'error')

    return redirect(url_for('performance.evaluation_list', period_id=period_id))


@performance_bp.route('/performance/view/<int:evaluation_id>')
def view_evaluation(evaluation_id):
    """View evaluation details."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    evaluation_data = get_evaluation_by_id(evaluation_id)

    if not evaluation_data:
        flash('التقييم غير موجود', 'error')
        return redirect(url_for('performance.evaluation_list'))

    return render_template('view_evaluation.html', evaluation_data=evaluation_data)


@performance_bp.route('/performance/employee/<int:employee_id>/history')
def employee_performance_history(employee_id):
    """Employee performance history."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_db_connection()
    employee = conn.execute('SELECT * FROM employees WHERE id = ?', (employee_id,)).fetchone()
    conn.close()

    if not employee:
        flash('الموظف غير موجود', 'error')
        return redirect(url_for('performance.evaluation_list'))

    evaluations = get_employee_evaluations(employee_id)
    trend = get_employee_performance_trend(employee_id)

    return render_template('employee_performance_history.html',
                         employee=employee,
                         evaluations=evaluations,
                         trend=trend)


@performance_bp.route('/performance/reports')
def performance_reports():
    """Performance reports."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    period_id = request.args.get('period_id')
    periods = get_evaluation_periods()

    stats = []
    criteria_analysis = []

    if period_id:
        stats = get_evaluation_statistics(period_id)
        criteria_analysis = get_criteria_performance_analysis(period_id)

    return render_template('performance_reports.html',
                         periods=periods,
                         selected_period_id=int(period_id) if period_id else None,
                         stats=stats,
                         criteria_analysis=criteria_analysis)


@performance_bp.route('/performance/employees')
def employees_with_evaluations():
    """Employees with evaluations."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    employees = get_employees_with_evaluations()
    return render_template('employees_with_evaluations.html', employees=employees)


# API Routes
@performance_bp.route('/api/performance/criteria')
def api_evaluation_criteria():
    """API to get evaluation criteria."""
    criteria = get_evaluation_criteria()
    return jsonify([dict(row) for row in criteria])


@performance_bp.route('/api/performance/periods')
def api_evaluation_periods():
    """API to get evaluation periods."""
    periods = get_evaluation_periods()
    return jsonify([dict(row) for row in periods])


@performance_bp.route('/api/performance/statistics/<int:period_id>')
def api_performance_statistics(period_id):
    """API to get performance statistics."""
    stats = get_evaluation_statistics(period_id)
    return jsonify([dict(row) for row in stats])


@performance_bp.route('/api/performance/employee/<int:employee_id>/trend')
def api_employee_performance_trend(employee_id):
    """API to get employee performance trend."""
    trend = get_employee_performance_trend(employee_id)
    return jsonify([dict(row) for row in trend])


@performance_bp.route('/api/performance/criteria_analysis/<int:period_id>')
def api_criteria_performance_analysis(period_id):
    """API for criteria performance analysis."""
    analysis = get_criteria_performance_analysis(period_id)
    return jsonify([dict(row) for row in analysis])


@performance_bp.route("/performance/export_evaluations/<int:period_id>")
def export_evaluations(period_id):
    """Export evaluations as JSON."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT employee_name, score, comments
        FROM evaluations
        WHERE period_id = ?
    """, (period_id,))
    data = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(data)
