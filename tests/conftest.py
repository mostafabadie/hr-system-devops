"""
Pytest configuration and shared fixtures.
"""
import pytest
import os
import tempfile
import sqlite3
from db import get_db_connection, init_db, ensure_employee_portal_columns, ensure_payroll_schema, ensure_indexes, DEFAULT_DB_PATH


@pytest.fixture
def app():
    """Create and configure a test app instance."""
    from app import app as flask_app
    flask_app.config['TESTING'] = True
    flask_app.config['SERVER_NAME'] = 'localhost'

    # Create a temporary database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)

    # Override the database path in db module
    import db
    original_path = db.DEFAULT_DB_PATH
    db.DEFAULT_DB_PATH = db_path

    yield flask_app

    # Cleanup: restore original path
    db.DEFAULT_DB_PATH = original_path
    # Close any open connections
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def client(app):
    """Create a test client with initialized database."""
    with app.test_client() as test_client:
        # Initialize the test database
        init_db()
        ensure_employee_portal_columns()
        ensure_payroll_schema()
        ensure_indexes()
        yield test_client


@pytest.fixture
def logged_in_client(client):
    """Create a test client with admin logged in."""
    with client.session_transaction() as sess:
        sess['logged_in'] = True
    return client


@pytest.fixture
def employee_client(client):
    """Create a test client with employee logged in."""
    with client.session_transaction() as sess:
        sess['employee_logged_in'] = True
        sess['employee_id'] = 1
        sess['employee_name'] = 'Test Employee'
    return client


@pytest.fixture
def tmp_db_path():
    """Create a temporary database path."""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)

    # Override the database path
    import db
    original_path = db.DEFAULT_DB_PATH
    db.DEFAULT_DB_PATH = db_path

    yield db_path

    # Restore and cleanup
    db.DEFAULT_DB_PATH = original_path
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def db_conn(tmp_db_path):
    """Create a direct database connection for testing."""
    conn = sqlite3.connect(tmp_db_path)
    conn.row_factory = sqlite3.Row

    # Initialize schema
    # We need to call init_db() which uses the overridden DEFAULT_DB_PATH
    init_db()
    ensure_employee_portal_columns()
    ensure_payroll_schema()
    ensure_indexes()

    yield conn

    conn.close()
