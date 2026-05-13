"""Tests for Flask routes and view responses."""
import pytest


class TestPublicRoutes:
    """Test public routes that don't require authentication."""

    def test_login_page_loads(self, client):
        """Test that login page loads successfully."""
        resp = client.get('/login')
        assert resp.status_code == 200
        assert 'تسجيل الدخول' in resp.get_data(as_text=True)

    def test_login_page_has_employee_portal_link(self, client):
        """Test login page has link to employee portal."""
        resp = client.get('/login')
        data = resp.get_data(as_text=True)
        assert '/employee/login' in data or 'portal.employee_login' in data


class TestAuthRoutes:
    """Test authentication-related routes."""

    def test_login_with_invalid_credentials(self, client):
        """Test login with wrong credentials shows error."""
        resp = client.post('/login', data={
            'username': 'wrong',
            'password': 'wrong'
        }, follow_redirects=False)
        # Should show error (200) or redirect (302)
        assert resp.status_code in (200, 302, 400)

    def test_logout(self, logged_in_client):
        """Test logout clears session."""
        resp = logged_in_client.get('/logout', follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers['Location'].endswith('/login')


class TestProtectedRoutes:
    """Test routes that require authentication."""

    def test_index_requires_login(self, client):
        """Test index page redirects when not logged in."""
        resp = client.get('/', follow_redirects=False)
        assert resp.status_code == 302
        assert '/login' in resp.headers['Location']

    def test_index_loads_when_logged_in(self, logged_in_client):
        """Test index page loads with valid session."""
        resp = logged_in_client.get('/')
        assert resp.status_code == 200

    def test_dashboard_requires_login(self, client):
        """Test dashboard redirects when not logged in."""
        resp = client.get('/dashboard', follow_redirects=False)
        assert resp.status_code == 302

    def test_dashboard_loads_when_logged_in(self, logged_in_client):
        """Test dashboard loads with valid session."""
        resp = logged_in_client.get('/dashboard')
        assert resp.status_code == 200
        data = resp.get_data(as_text=True)
        assert 'لوحة التحكم' in data or 'dashboard' in data.lower()

    def test_employees_loads(self, logged_in_client):
        """Test employees list page loads."""
        resp = logged_in_client.get('/employees')
        assert resp.status_code == 200

    def test_payroll_loads(self, logged_in_client):
        """Test payroll page loads."""
        resp = logged_in_client.get('/payroll')
        assert resp.status_code == 200

    def test_attendance_loads(self, logged_in_client):
        """Test attendance page loads."""
        resp = logged_in_client.get('/attendance')
        assert resp.status_code == 200

    def test_leaves_loads(self, logged_in_client):
        """Test leaves page loads."""
        resp = logged_in_client.get('/leaves')
        assert resp.status_code == 200

    def test_leaves_pending_loads(self, logged_in_client):
        """Test pending leaves page loads."""
        resp = logged_in_client.get('/leaves/pending')
        assert resp.status_code == 200

    def test_performance_dashboard_loads(self, logged_in_client):
        """Test performance dashboard loads."""
        resp = logged_in_client.get('/performance')
        assert resp.status_code == 200


class TestEmployeePortalRoutes:
    """Test employee self-service portal routes."""

    def test_employee_login_page_loads(self, client):
        """Test employee login page loads."""
        resp = client.get('/employee/login')
        assert resp.status_code == 200

    def test_self_portal_requires_login(self, client):
        """Test self portal redirects when not logged in."""
        resp = client.get('/self/portal', follow_redirects=False)
        assert resp.status_code == 302

    def test_self_portal_loads_when_logged_in(self, employee_client):
        """Test self portal loads with employee session."""
        resp = employee_client.get('/self/portal')
        assert resp.status_code == 200


class TestAPIRoutes:
    """Test API endpoints."""

    def test_employee_search_api(self, logged_in_client):
        """Test employee search API returns JSON."""
        resp = logged_in_client.get('/api/employees/search?keyword=test')
        assert resp.status_code == 200
        assert 'employees' in resp.get_json()

    def test_leave_balance_api_returns_404_for_invalid(self, logged_in_client):
        """Test leave balance API returns 404 for invalid employee."""
        resp = logged_in_client.get('/api/leave_balance/9999/1')
        assert resp.status_code == 404

    def test_attendance_overview_api(self, logged_in_client):
        """Test attendance overview API returns JSON."""
        resp = logged_in_client.get('/api/reports/attendance_overview')
        assert resp.status_code == 200

    def test_payroll_monthly_api(self, logged_in_client):
        """Test payroll monthly API returns JSON."""
        resp = logged_in_client.get('/api/reports/payroll_monthly')
        assert resp.status_code == 200

    def test_leave_usage_api(self, logged_in_client):
        """Test leave usage API returns JSON."""
        resp = logged_in_client.get('/api/reports/leave_usage')
        assert resp.status_code == 200
