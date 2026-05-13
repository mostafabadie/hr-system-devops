"""API endpoints for employee management."""
from flask_restx import Namespace, Resource, fields
from db import get_db_connection
from datetime import datetime

# Create namespace
ns = Namespace('employees', description='Employee management operations')

# Define models for request/response validation
employee_model = ns.model('Employee', {
    'id': fields.Integer(readonly=True, description='Employee ID'),
    'name': fields.String(required=True, description='Employee name'),
    'department': fields.String(description='Department'),
    'position': fields.String(description='Position'),
    'salary': fields.Float(description='Salary'),
    'phone': fields.String(description='Phone number'),
    'email': fields.String(description='Email address'),
    'address': fields.String(description='Address'),
    'username': fields.String(description='Portal username'),
    'document': fields.String(description='CV document filename')
})

employee_input = ns.model('EmployeeInput', {
    'name': fields.String(required=True, description='Employee name'),
    'department': fields.String(description='Department'),
    'position': fields.String(description='Position'),
    'salary': fields.Float(description='Salary'),
    'phone': fields.String(description='Phone number'),
    'email': fields.String(description='Email address'),
    'address': fields.String(description='Address'),
    'username': fields.String(description='Portal username'),
    'password': fields.String(description='Portal password')
})

@ns.route('/')
class EmployeeList(Resource):
    @ns.doc('list_employees')
    @ns.marshal_list_with(employee_model)
    def get(self):
        """List all employees"""
        conn = get_db_connection()
        employees = conn.execute('SELECT * FROM employees ORDER BY name').fetchall()
        conn.close()
        return [dict(emp) for emp in employees]

    @ns.doc('create_employee')
    @ns.expect(employee_input)
    @ns.marshal_with(employee_model, code=201)
    def post(self):
        """Create a new employee"""
        from werkzeug.security import generate_password_hash

        data = ns.payload
        conn = get_db_connection()

        try:
            # Hash password if provided
            password_hash = None
            if data.get('password'):
                password_hash = generate_password_hash(data['password'])

            cursor = conn.execute(
                '''INSERT INTO employees
                   (name, department, position, salary, phone, email, address, username, password_hash)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    data['name'],
                    data.get('department'),
                    data.get('position'),
                    data.get('salary', 0),
                    data.get('phone'),
                    data.get('email'),
                    data.get('address'),
                    data.get('username'),
                    password_hash
                )
            )
            conn.commit()

            # Get the created employee
            employee_id = cursor.lastrowid
            employee = conn.execute('SELECT * FROM employees WHERE id = ?', (employee_id,)).fetchone()
            conn.close()
            return dict(employee), 201
        except Exception as e:
            conn.rollback()
            conn.close()
            ns.abort(400, str(e))

@ns.route('/<int:id>')
@ns.param('id', 'The employee identifier')
@ns.response(404, 'Employee not found')
class Employee(Resource):
    @ns.doc('get_employee')
    @ns.marshal_with(employee_model)
    def get(self, id):
        """Fetch an employee given its identifier"""
        conn = get_db_connection()
        employee = conn.execute('SELECT * FROM employees WHERE id = ?', (id,)).fetchone()
        conn.close()
        if not employee:
            ns.abort(404, f"Employee {id} not found")
        return dict(employee)

    @ns.doc('update_employee')
    @ns.expect(employee_input)
    @ns.marshal_with(employee_model)
    def put(self, id):
        """Update an employee given its identifier"""
        from werkzeug.security import generate_password_hash

        data = ns.payload
        conn = get_db_connection()

        try:
            # Check if employee exists
            employee = conn.execute('SELECT * FROM employees WHERE id = ?', (id,)).fetchone()
            if not employee:
                conn.close()
                ns.abort(404, f"Employee {id} not found")

            # Prepare update fields
            update_fields = []
            values = []

            for field in ['name', 'department', 'position', 'salary', 'phone', 'email', 'address', 'username']:
                if field in data:
                    update_fields.append(f"{field} = ?")
                    values.append(data[field])

            # Handle password separately
            if 'password' in data and data['password']:
                update_fields.append("password_hash = ?")
                values.append(generate_password_hash(data['password']))

            if not update_fields:
                conn.close()
                ns.abort(400, "No fields to update")

            values.append(id)
            query = f"UPDATE employees SET {', '.join(update_fields)} WHERE id = ?"
            conn.execute(query, values)
            conn.commit()

            # Get updated employee
            employee = conn.execute('SELECT * FROM employees WHERE id = ?', (id,)).fetchone()
            conn.close()
            return dict(employee)
        except Exception as e:
            conn.rollback()
            conn.close()
            ns.abort(400, str(e))

    @ns.doc('delete_employee')
    @ns.response(204, 'Employee deleted')
    def delete(self, id):
        """Delete an employee given its identifier"""
        conn = get_db_connection()
        employee = conn.execute('SELECT * FROM employees WHERE id = ?', (id,)).fetchone()
        if not employee:
            conn.close()
            ns.abort(404, f"Employee {id} not found")

        conn.execute('DELETE FROM employees WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        return '', 204

@ns.route('/<int:id>/attendance')
@ns.param('id', 'The employee identifier')
class EmployeeAttendance(Resource):
    @ns.doc('get_employee_attendance')
    def get(self, id):
        """Get attendance records for an employee"""
        conn = get_db_connection()
        attendance = conn.execute(
            'SELECT * FROM attendance WHERE employee_id = ? ORDER BY date DESC',
            (id,)
        ).fetchall()
        conn.close()
        return [dict(record) for record in attendance]

@ns.route('/search')
class EmployeeSearch(Resource):
    @ns.doc('search_employees')
    @ns.param('q', 'Search query for name, email, or department')
    @ns.param('page', 'Page number', type=int, default=1)
    @ns.param('per_page', 'Items per page', type=int, default=20)
    @ns.marshal_list_with(employee_model)
    def get(self):
        """Search employees"""
        from flask import request

        query = request.args.get('q', '').strip()
        page = max(int(request.args.get('page', 1)), 1)
        per_page = min(max(int(request.args.get('per_page', 20)), 1), 100)
        offset = (page - 1) * per_page

        conn = get_db_connection()

        if query:
            like = f'%{query}%'
            employees = conn.execute(
                '''SELECT * FROM employees
                   WHERE name LIKE ? OR email LIKE ? OR department LIKE ?
                   ORDER BY name
                   LIMIT ? OFFSET ?''',
                (like, like, like, per_page, offset)
            ).fetchall()

            total = conn.execute(
                '''SELECT COUNT(*) FROM employees
                   WHERE name LIKE ? OR email LIKE ? OR department LIKE ?''',
                (like, like, like)
            ).fetchone()[0]
        else:
            employees = conn.execute(
                'SELECT * FROM employees ORDER BY name LIMIT ? OFFSET ?',
                (per_page, offset)
            ).fetchall()

            total = conn.execute('SELECT COUNT(*) FROM employees').fetchone()[0]

        conn.close()

        # Add pagination headers
        from flask import Response
        response = [dict(emp) for emp in employees]
        return response

# Register namespace with API
def register_namespace(api):
    api.add_namespace(ns)