"""Administrative dashboard for system monitoring and health checks."""
from flask import Blueprint, redirect, render_template, jsonify, request, session, url_for
from db import get_db_connection
import sqlite3
import time
import psutil
import os
from datetime import datetime, timedelta

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def get_system_stats():
    """Get system statistics for monitoring."""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used = memory.used / (1024 ** 3)  # GB
        memory_total = memory.total / (1024 ** 3)  # GB

        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used = disk.used / (1024 ** 3)  # GB
        disk_total = disk.total / (1024 ** 3)  # GB

        # Boot time
        boot_time = datetime.fromtimestamp(psutil.boot_time())

        return {
            'cpu': {
                'percent': cpu_percent,
                'status': 'good' if cpu_percent < 80 else 'warning' if cpu_percent < 95 else 'critical'
            },
            'memory': {
                'percent': memory_percent,
                'used_gb': round(memory_used, 2),
                'total_gb': round(memory_total, 2),
                'status': 'good' if memory_percent < 80 else 'warning' if memory_percent < 95 else 'critical'
            },
            'disk': {
                'percent': disk_percent,
                'used_gb': round(disk_used, 2),
                'total_gb': round(disk_total, 2),
                'status': 'good' if disk_percent < 80 else 'warning' if disk_percent < 95 else 'critical'
            },
            'boot_time': boot_time.strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        # Fallback if psutil is not available
        return {
            'cpu': {'percent': 0, 'status': 'unknown'},
            'memory': {'percent': 0, 'used_gb': 0, 'total_gb': 0, 'status': 'unknown'},
            'disk': {'percent': 0, 'used_gb': 0, 'total_gb': 0, 'status': 'unknown'},
            'boot_time': 'Unknown',
            'error': str(e)
        }

def get_db_stats():
    """Get database statistics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get table sizes
        tables = ['employees', 'leave_requests', 'performance_evaluations', 'payrolls', 'attendance']
        table_stats = {}

        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()['count']
                table_stats[table] = count
            except sqlite3.OperationalError:
                table_stats[table] = 0  # Table might not exist

        # Get database file size
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'hr.db')
        db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0

        conn.close()

        return {
            'tables': table_stats,
            'size_mb': round(db_size / (1024 * 1024), 2),
            'status': 'good'
        }
    except Exception as e:
        return {
            'tables': {},
            'size_mb': 0,
            'status': 'error',
            'error': str(e)
        }

def get_recent_activities(limit=10):
    """Get recent user activities from logs or activity table."""
    try:
        conn = get_db_connection()
        # This would typically come from an activity log table
        # For now, we'll simulate with recent login/logout or other trackable events
        activities = []

        # Get recent employees added (as an example of activity)
        cursor = conn.execute("""
            SELECT name, 'Employee Added' as action,
                   datetime('now') as timestamp
            FROM employees
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))

        for row in cursor.fetchall():
            activities.append({
                'user': 'System',  # In a real app, this would be the actual user
                'action': row['action'],
                'details': f"Employee: {row['name']}",
                'timestamp': row['timestamp']
            })

        conn.close()
        return activities
    except Exception as e:
        return [{'error': str(e)}]

@admin_bp.route('/')
def admin_dashboard():
    """Admin dashboard home page."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Check if user is admin (you might want to implement proper role checking)
    # For now, we'll allow any logged-in user to access admin dashboard
    # In production, you should check for admin role/permissions

    system_stats = get_system_stats()
    db_stats = get_db_stats()
    recent_activities = get_recent_activities()

    return render_template('admin/dashboard.html',
                         system_stats=system_stats,
                         db_stats=db_stats,
                         recent_activities=recent_activities)

@admin_bp.route('/health')
def health_check():
    """Health check endpoint for monitoring systems."""
    system_stats = get_system_stats()
    db_stats = get_db_stats()

    # Determine overall health status
    health_status = 'healthy'
    issues = []

    if system_stats['cpu']['status'] in ['warning', 'critical']:
        health_status = 'degraded'
        issues.append(f"High CPU usage: {system_stats['cpu']['percent']}%")

    if system_stats['memory']['status'] in ['warning', 'critical']:
        health_status = 'degraded'
        issues.append(f"High memory usage: {system_stats['memory']['percent']}%")

    if system_stats['disk']['status'] in ['warning', 'critical']:
        health_status = 'degraded'
        issues.append(f"High disk usage: {system_stats['disk']['percent']}%")

    if db_stats['status'] == 'error':
        health_status = 'unhealthy'
        issues.append("Database connection error")

    response = {
        'status': health_status,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'system': system_stats,
        'database': db_stats,
        'issues': issues
    }

    status_code = 200 if health_status == 'healthy' else 503 if health_status == 'unhealthy' else 200
    return jsonify(response), status_code

@admin_bp.route('/metrics')
def metrics():
    """Prometheus-style metrics endpoint."""
    system_stats = get_system_stats()
    db_stats = get_db_stats()

    metrics_lines = []

    # System metrics
    metrics_lines.append(f"hr_system_cpu_usage_percent {system_stats['cpu']['percent']}")
    metrics_lines.append(f"hr_system_memory_usage_percent {system_stats['memory']['percent']}")
    metrics_lines.append(f"hr_system_memory_used_gb {system_stats['memory']['used_gb']}")
    metrics_lines.append(f"hr_system_disk_usage_percent {system_stats['disk']['percent']}")
    metrics_lines.append(f"hr_system_disk_used_gb {system_stats['disk']['used_gb']}")

    # Database metrics
    for table, count in db_stats['tables'].items():
        metrics_lines.append(f"hr_system_db_table_{table}_count {count}")

    metrics_lines.append(f"hr_system_db_size_mb {db_stats['size_mb']}")

    return '\n'.join(metrics_lines), 200, {'Content-Type': 'text/plain'}

@admin_bp.route('/activities')
def activities():
    """Get user activities."""
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401

    limit = request.args.get('limit', 50, type=int)
    activities = get_recent_activities(limit)
    return jsonify({'activities': activities})

@admin_bp.route('/query-performance')
def query_performance():
    """Monitor database query performance."""
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401

    # This would typically query a query performance table or log
    # For demonstration, we'll run some sample queries and time them
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        queries_to_test = [
            ("Employee count", "SELECT COUNT(*) FROM employees"),
            ("Recent employees", "SELECT * FROM employees ORDER BY id DESC LIMIT 10"),
            ("Leave requests count", "SELECT COUNT(*) FROM leave_requests"),
            ("Performance evaluations count", "SELECT COUNT(*) FROM performance_evaluations")
        ]

        results = []
        for query_name, query in queries_to_test:
            start_time = time.time()
            try:
                cursor.execute(query)
                cursor.fetchall()  # Consume results
                end_time = time.time()
                execution_time = (end_time - start_time) * 1000  # Convert to milliseconds

                results.append({
                    'query': query_name,
                    'sql': query,
                    'execution_time_ms': round(execution_time, 2),
                    'status': 'success'
                })
            except Exception as e:
                end_time = time.time()
                execution_time = (end_time - start_time) * 1000
                results.append({
                    'query': query_name,
                    'sql': query,
                    'execution_time_ms': round(execution_time, 2),
                    'status': 'error',
                    'error': str(e)
                })

        conn.close()
        return jsonify({'query_performance': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500