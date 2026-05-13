"""Tests for database operations in db.py."""
import pytest
import sqlite3


class TestGetDbConnection:
    """Test get_db_connection function."""

    def test_returns_connection(self, tmp_db_path):
        """Test that get_db_connection returns a sqlite3 connection."""
        from db import get_db_connection
        conn = get_db_connection(tmp_db_path)
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_sets_row_factory(self, tmp_db_path):
        """Test that connection has Row factory set."""
        from db import get_db_connection
        conn = get_db_connection(tmp_db_path)
        # Create a test table and query it
        conn.execute('CREATE TABLE test (id INTEGER)')
        conn.execute('INSERT INTO test VALUES (1)')
        row = conn.execute('SELECT * FROM test').fetchone()
        assert isinstance(row, sqlite3.Row)
        conn.close()

    def test_default_path(self):
        """Test connection with default path."""
        from db import get_db_connection, DEFAULT_DB_PATH
        # This should use the default path
        conn = get_db_connection()
        assert conn is not None
        # Check it's connected to the default DB
        result = conn.execute("SELECT 1").fetchone()
        assert result[0] == 1
        conn.close()


class TestInitDb:
    """Test init_db function creates all required tables."""

    def test_creates_employees_table(self, db_conn):
        """Test employees table exists."""
        cursor = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='employees'"
        )
        assert cursor.fetchone() is not None

    def test_creates_attendance_table(self, db_conn):
        """Test attendance table exists."""
        cursor = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='attendance'"
        )
        assert cursor.fetchone() is not None

    def test_creates_leave_requests_table(self, db_conn):
        """Test leave_requests table exists."""
        cursor = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='leave_requests'"
        )
        assert cursor.fetchone() is not None

    def test_creates_leave_types_table(self, db_conn):
        """Test leave_types table exists."""
        cursor = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='leave_types'"
        )
        assert cursor.fetchone() is not None

    def test_creates_payrolls_table(self, db_conn):
        """Test payrolls table exists."""
        cursor = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='payrolls'"
        )
        assert cursor.fetchone() is not None

    def test_creates_employee_leave_balance_table(self, db_conn):
        """Test employee_leave_balance table exists."""
        cursor = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='employee_leave_balance'"
        )
        assert cursor.fetchone() is not None

    def test_creates_evaluation_criteria_table(self, db_conn):
        """Test evaluation_criteria table exists."""
        cursor = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='evaluation_criteria'"
        )
        assert cursor.fetchone() is not None

    def test_creates_evaluation_periods_table(self, db_conn):
        """Test evaluation_periods table exists."""
        cursor = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='evaluation_periods'"
        )
        assert cursor.fetchone() is not None

    def test_creates_performance_evaluations_table(self, db_conn):
        """Test performance_evaluations table exists."""
        cursor = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='performance_evaluations'"
        )
        assert cursor.fetchone() is not None

    def test_creates_evaluation_details_table(self, db_conn):
        """Test evaluation_details table exists."""
        cursor = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='evaluation_details'"
        )
        assert cursor.fetchone() is not None

    def test_creates_daily_attendance_summary_table(self, db_conn):
        """Test daily_attendance_summary table exists."""
        cursor = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='daily_attendance_summary'"
        )
        assert cursor.fetchone() is not None

    def test_default_leave_types_created(self, db_conn):
        """Test that default leave types are created."""
        cursor = db_conn.execute('SELECT COUNT(*) as c FROM leave_types')
        count = cursor.fetchone()['c']
        assert count > 0


class TestEnsureEmployeePortalColumns:
    """Test ensure_employee_portal_columns function."""

    def test_adds_username_column(self, db_conn):
        """Test that username column is added to employees."""
        # Check column exists
        cursor = db_conn.execute("PRAGMA table_info(employees)")
        columns = [row['name'] for row in cursor.fetchall()]
        assert 'username' in columns

    def test_adds_password_hash_column(self, db_conn):
        """Test that password_hash column is added to employees."""
        cursor = db_conn.execute("PRAGMA table_info(employees)")
        columns = [row['name'] for row in cursor.fetchall()]
        assert 'password_hash' in columns

    def test_adds_address_column(self, db_conn):
        """Test that address column is added to employees."""
        cursor = db_conn.execute("PRAGMA table_info(employees)")
        columns = [row['name'] for row in cursor.fetchall()]
        assert 'address' in columns


class TestEnsurePayrollSchema:
    """Test ensure_payroll_schema function."""

    def test_adds_month_column(self, db_conn):
        """Test that month column is added to payrolls if missing."""
        cursor = db_conn.execute("PRAGMA table_info(payrolls)")
        columns = [row['name'] for row in cursor.fetchall()]
        assert 'month' in columns


class TestEnsureIndexes:
    """Test ensure_indexes function."""

    def test_creates_indexes(self, db_conn):
        """Test that indexes are created."""
        cursor = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
        )
        indexes = cursor.fetchall()
        assert len(indexes) > 0
