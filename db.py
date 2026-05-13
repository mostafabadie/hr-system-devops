"""Centralized database module for the HR system."""
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "data", "hr.db")


def get_db_connection(db_path=None):
    """Create a connection to the SQLite database."""
    path = db_path or DEFAULT_DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize ALL database tables if they don't exist."""
    conn = get_db_connection()
    c = conn.cursor()

    # Employees table
    c.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        department TEXT,
        position TEXT,
        salary REAL,
        username TEXT UNIQUE,
        password_hash TEXT,
        phone TEXT,
        email TEXT,
        document TEXT,
        basic_salary REAL,
        address TEXT
    )
    """)

    # Attendance table
    c.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        date TEXT,
        check_in TEXT,
        check_out TEXT,
        FOREIGN KEY(employee_id) REFERENCES employees(id)
    )
    """)

    # Payrolls table
    c.execute("""
    CREATE TABLE IF NOT EXISTS payrolls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        salary REAL NOT NULL,
        bonus REAL DEFAULT 0,
        deductions REAL DEFAULT 0,
        net_salary REAL NOT NULL,
        payment_date TEXT NOT NULL,
        month TEXT,
        FOREIGN KEY(employee_id) REFERENCES employees(id)
    )
    """)

    # Payroll items table
    c.execute("""
    CREATE TABLE IF NOT EXISTS payroll_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payroll_id INTEGER NOT NULL,
        item_type TEXT NOT NULL,
        label TEXT NOT NULL,
        amount REAL NOT NULL,
        FOREIGN KEY(payroll_id) REFERENCES payrolls(id)
    )
    """)

    # Leave types table
    c.execute("""
    CREATE TABLE IF NOT EXISTS leave_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        max_days INTEGER NOT NULL DEFAULT 30
    )
    """)

    # Default leave types
    c.execute("""
        INSERT OR IGNORE INTO leave_types (name, max_days) VALUES
            ('Annual Leave', 21),
            ('Sick Leave', 15),
            ('Unpaid Leave', 30),
            ('Maternity Leave', 90),
            ('Emergency Leave', 7)
    """)

    # Leave requests table
    c.execute("""
    CREATE TABLE IF NOT EXISTS leave_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        leave_type_id INTEGER NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        days_requested INTEGER NOT NULL,
        reason TEXT,
        status TEXT DEFAULT 'pending',
        request_date TEXT,
        approved_by INTEGER,
        approved_date TEXT,
        comments TEXT,
        FOREIGN KEY(employee_id) REFERENCES employees(id),
        FOREIGN KEY(leave_type_id) REFERENCES leave_types(id)
    )
    """)

    # Employee leave balance table
    c.execute("""
    CREATE TABLE IF NOT EXISTS employee_leave_balance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        leave_type_id INTEGER NOT NULL,
        year INTEGER NOT NULL,
        allocated_days INTEGER NOT NULL,
        used_days INTEGER DEFAULT 0,
        remaining_days INTEGER NOT NULL,
        FOREIGN KEY(employee_id) REFERENCES employees(id),
        FOREIGN KEY(leave_type_id) REFERENCES leave_types(id),
        UNIQUE(employee_id, leave_type_id, year)
    )
    """)

    # Evaluation criteria table
    c.execute("""
    CREATE TABLE IF NOT EXISTS evaluation_criteria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        weight REAL DEFAULT 1.0,
        is_active INTEGER DEFAULT 1
    )
    """)

    # Evaluation periods table
    c.execute("""
    CREATE TABLE IF NOT EXISTS evaluation_periods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        year INTEGER NOT NULL,
        quarter INTEGER NOT NULL,
        is_active INTEGER DEFAULT 0
    )
    """)

    # Performance evaluations table
    c.execute("""
    CREATE TABLE IF NOT EXISTS performance_evaluations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        period_id INTEGER NOT NULL,
        evaluator_id INTEGER,
        overall_rating TEXT,
        overall_score REAL,
        strengths TEXT,
        areas_for_improvement TEXT,
        goals_next_period TEXT,
        comments TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT,
        completed_at TEXT,
        FOREIGN KEY(employee_id) REFERENCES employees(id),
        FOREIGN KEY(period_id) REFERENCES evaluation_periods(id)
    )
    """)

    # Evaluation details table (per-criterion scores)
    c.execute("""
    CREATE TABLE IF NOT EXISTS evaluation_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        evaluation_id INTEGER NOT NULL,
        criterion_id INTEGER NOT NULL,
        rating TEXT,
        score REAL,
        comments TEXT,
        FOREIGN KEY(evaluation_id) REFERENCES performance_evaluations(id),
        FOREIGN KEY(criterion_id) REFERENCES evaluation_criteria(id)
    )
    """)

    # Daily attendance summary table
    c.execute("""
    CREATE TABLE IF NOT EXISTS daily_attendance_summary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        total_hours_worked REAL,
        is_absent INTEGER DEFAULT 0,
        is_late INTEGER DEFAULT 0,
        is_early_departure INTEGER DEFAULT 0,
        FOREIGN KEY(employee_id) REFERENCES employees(id),
        UNIQUE(employee_id, date)
    )
    """)

    # Monthly payroll summary table
    c.execute("""
    CREATE TABLE IF NOT EXISTS monthly_payroll_summary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        month TEXT NOT NULL,
        total_salary REAL DEFAULT 0,
        total_bonus REAL DEFAULT 0,
        total_deductions REAL DEFAULT 0,
        net_salary REAL DEFAULT 0,
        FOREIGN KEY(employee_id) REFERENCES employees(id),
        UNIQUE(employee_id, month)
    )
    """)

    # Annual leave summary table
    c.execute("""
    CREATE TABLE IF NOT EXISTS annual_leave_summary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        leave_type_id INTEGER NOT NULL,
        year INTEGER NOT NULL,
        days_allocated INTEGER DEFAULT 0,
        days_used INTEGER DEFAULT 0,
        days_remaining INTEGER DEFAULT 0,
        FOREIGN KEY(employee_id) REFERENCES employees(id),
        FOREIGN KEY(leave_type_id) REFERENCES leave_types(id),
        UNIQUE(employee_id, leave_type_id, year)
    )
    """)

    conn.commit()
    conn.close()


def ensure_employee_portal_columns():
    """Add username and password_hash columns if they don't exist."""
    conn = get_db_connection()
    c = conn.cursor()
    info = c.execute("PRAGMA table_info(employees)").fetchall()
    col_names = [row[1] for row in info]
    if 'username' not in col_names:
        c.execute("ALTER TABLE employees ADD COLUMN username TEXT")
    if 'password_hash' not in col_names:
        c.execute("ALTER TABLE employees ADD COLUMN password_hash TEXT")
    if 'address' not in col_names:
        c.execute("ALTER TABLE employees ADD COLUMN address TEXT")
    if 'basic_salary' not in col_names:
        c.execute("ALTER TABLE employees ADD COLUMN basic_salary REAL")
    conn.commit()
    conn.close()


def ensure_payroll_schema():
    """Ensure payroll table columns exist (legacy support)."""
    conn = get_db_connection()
    c = conn.cursor()

    cols = [r[1] for r in c.execute("PRAGMA table_info(payrolls)").fetchall()]
    for col_name, ddl in [
        ("salary", "salary REAL"),
        ("bonus", "bonus REAL DEFAULT 0"),
        ("deductions", "deductions REAL DEFAULT 0"),
        ("net_salary", "net_salary REAL"),
        ("payment_date", "payment_date TEXT"),
        ("month", "month TEXT"),
    ]:
        if col_name not in cols:
            try:
                c.execute(f"ALTER TABLE payrolls ADD COLUMN {ddl}")
            except sqlite3.OperationalError:
                pass

    conn.commit()
    conn.close()


def ensure_evaluation_periods_status():
    """Add status and created_date columns to evaluation_periods if missing, and migrate data."""
    conn = get_db_connection()
    c = conn.cursor()
    cols = [r[1] for r in c.execute("PRAGMA table_info(evaluation_periods)").fetchall()]

    if 'status' not in cols:
        try:
            c.execute("ALTER TABLE evaluation_periods ADD COLUMN status TEXT DEFAULT 'completed'")
            # Migrate existing data from is_active to status
            c.execute("UPDATE evaluation_periods SET status = 'active' WHERE is_active = 1 AND status IS NULL")
            c.execute("UPDATE evaluation_periods SET status = 'completed' WHERE (is_active IS NULL OR is_active = 0) AND status IS NULL")
        except sqlite3.OperationalError:
            pass

    if 'created_date' not in cols:
        try:
            c.execute("ALTER TABLE evaluation_periods ADD COLUMN created_date TEXT DEFAULT CURRENT_TIMESTAMP")
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()


def ensure_indexes():
    """Create indexes for better query performance."""
    conn = get_db_connection()
    c = conn.cursor()
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_employees_name ON employees(name)",
        "CREATE INDEX IF NOT EXISTS idx_employees_email ON employees(email)",
        "CREATE INDEX IF NOT EXISTS idx_employees_department ON employees(department)",
        "CREATE INDEX IF NOT EXISTS idx_payrolls_employee_id ON payrolls(employee_id)",
        "CREATE INDEX IF NOT EXISTS idx_payrolls_payment_date ON payrolls(payment_date DESC)",
        "CREATE INDEX IF NOT EXISTS idx_attendance_employee_date ON attendance(employee_id, date)",
        "CREATE INDEX IF NOT EXISTS idx_leave_requests_employee ON leave_requests(employee_id)",
        "CREATE INDEX IF NOT EXISTS idx_leave_requests_status ON leave_requests(status)",
        "CREATE INDEX IF NOT EXISTS idx_perf_eval_employee ON performance_evaluations(employee_id)",
        "CREATE INDEX IF NOT EXISTS idx_perf_eval_period ON performance_evaluations(period_id)",
    ]
    for idx_sql in indexes:
        try:
            c.execute(idx_sql)
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()
