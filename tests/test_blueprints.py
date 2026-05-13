"""Tests for Blueprint registration and route endpoints."""
import pytest


EXPECTED_BLUEPRINTS = [
    'employees',
    'leaves',
    'performance',
    'portal',
    'reports',
]


class TestBlueprintRegistration:
    """Test that all Blueprints are properly registered."""

    def test_all_blueprints_registered(self, app):
        """Test that all expected Blueprints are registered."""
        registered_blueprints = [bp.name for bp in app.blueprints.values()]
        for bp_name in EXPECTED_BLUEPRINTS:
            assert bp_name in registered_blueprints, \
                f"Blueprint '{bp_name}' not registered"

    def test_no_duplicate_endpoints(self, app):
        """Test that there are no duplicate endpoint names."""
        endpoints = [rule.endpoint for rule in app.url_map.iter_rules()]
        assert len(endpoints) == len(set(endpoints)), \
            "Duplicate endpoints found"


class TestEndpointExists:
    """Test that key endpoints exist."""

    def test_employees_endpoints(self, app):
        """Test employees Blueprint endpoints exist."""
        expected = [
            'employees.employees',
            'employees.add_employee',
            'employees.employee_details',
            'employees.edit_employee',
            'employees.delete_employee',
            'employees.attendance',
            'employees.payroll',
            'employees.add_payroll',
        ]
        for endpoint in expected:
            assert any(rule.endpoint == endpoint for rule in app.url_map.iter_rules()), \
                f"Endpoint '{endpoint}' not found"

    def test_leaves_endpoints(self, app):
        """Test leaves Blueprint endpoints exist."""
        expected = [
            'leaves.leaves',
            'leaves.pending_leaves',
            'leaves.request_leave',
            'leaves.approve_leave',
            'leaves.reject_leave',
            'leaves.leave_balance',
        ]
        for endpoint in expected:
            assert any(rule.endpoint == endpoint for rule in app.url_map.iter_rules()), \
                f"Endpoint '{endpoint}' not found"

    def test_performance_endpoints(self, app):
        """Test performance Blueprint endpoints exist."""
        expected = [
            'performance.performance_dashboard',
            'performance.evaluation_periods',
            'performance.create_period',
            'performance.evaluation_list',
            'performance.evaluate_employee',
            'performance.submit_evaluation',
        ]
        for endpoint in expected:
            assert any(rule.endpoint == endpoint for rule in app.url_map.iter_rules()), \
                f"Endpoint '{endpoint}' not found"

    def test_portal_endpoints(self, app):
        """Test portal Blueprint endpoints exist."""
        expected = [
            'portal.employee_login',
            'portal.employee_logout',
            'portal.self_portal',
            'portal.self_request_leave',
            'portal.self_performance_history',
            'portal.self_payroll',
        ]
        for endpoint in expected:
            assert any(rule.endpoint == endpoint for rule in app.url_map.iter_rules()), \
                f"Endpoint '{endpoint}' not found"

    def test_reports_endpoints(self, app):
        """Test reports Blueprint endpoints exist."""
        expected = [
            'reports.dashboard',
            'reports.leave_reports',
        ]
        for endpoint in expected:
            assert any(rule.endpoint == endpoint for rule in app.url_map.iter_rules()), \
                f"Endpoint '{endpoint}' not found"


class TestUrlForBuilding:
    """Test that url_for can build all expected endpoints."""

    def test_employees_url_for(self, app):
        """Test url_for works for employees endpoints."""
        with app.app_context():
            from flask import url_for
            # These should not raise BuildError
            url_for('employees.employees')
            url_for('employees.add_employee')
            url_for('employees.employee_details', emp_id=1)
            url_for('employees.edit_employee', id=1)
            url_for('employees.delete_employee', id=1)

    def test_leaves_url_for(self, app):
        """Test url_for works for leaves endpoints."""
        with app.app_context():
            from flask import url_for
            url_for('leaves.leaves')
            url_for('leaves.pending_leaves')
            url_for('leaves.request_leave')
            url_for('leaves.my_leave_requests', employee_id=1)
            url_for('leaves.approve_leave', request_id=1)
            url_for('leaves.reject_leave', request_id=1)

    def test_performance_url_for(self, app):
        """Test url_for works for performance endpoints."""
        with app.app_context():
            from flask import url_for
            url_for('performance.performance_dashboard')
            url_for('performance.evaluation_periods')
            url_for('performance.evaluation_list')
            url_for('performance.evaluate_employee', employee_id=1)

    def test_portal_url_for(self, app):
        """Test url_for works for portal endpoints."""
        with app.app_context():
            from flask import url_for
            url_for('portal.employee_login')
            url_for('portal.self_portal')
            url_for('portal.self_request_leave')
            url_for('portal.self_performance_history')
            url_for('portal.self_payroll')

    def test_reports_url_for(self, app):
        """Test url_for works for reports endpoints."""
        with app.app_context():
            from flask import url_for
            url_for('reports.dashboard')
            url_for('reports.leave_reports')
