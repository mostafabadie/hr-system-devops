"""Database utility helpers for standardized database operations."""
from contextlib import contextmanager
from db import get_db_connection
import sqlite3
from typing import Optional, Any, List, Tuple, Dict


@contextmanager
def get_db_cursor(commit: bool = False):
    """Context manager for database connections with automatic cleanup.

    Args:
        commit: Whether to commit changes before closing connection

    Yields:
        sqlite3.Cursor: Database cursor for executing queries
    """
    conn = None
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        yield cursor
        if commit:
            conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()


def execute_query(query: str, params: Tuple = (), fetch: str = None) -> Any:
    """Execute a query and return results based on fetch parameter.

    Args:
        query: SQL query string
        params: Query parameters as tuple
        fetch: 'one' for single row, 'all' for all rows, None for no return

    Returns:
        Query results based on fetch parameter:
        - 'one': Single row as sqlite3.Row or None
        - 'all': List of rows as sqlite3.Row or empty list
        - None: None (for INSERT/UPDATE/DELETE operations)
    """
    with get_db_cursor(commit=(fetch is None)) as cursor:
        cursor.execute(query, params)
        if fetch == 'one':
            return cursor.fetchone()
        elif fetch == 'all':
            return cursor.fetchall()
        return None


def execute_many(query: str, params_list: List[Tuple]) -> None:
    """Execute a query multiple times with different parameters.

    Args:
        query: SQL query string
        params_list: List of parameter tuples
    """
    with get_db_cursor(commit=True) as cursor:
        cursor.executemany(query, params_list)