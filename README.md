# HR Management System

A Flask-based Human Resources management system with employee management, leave tracking, performance evaluation, and reporting features.

## Project Structure

```
hr-system/
├── app.py                    # Main Flask application
├── config.py                 # Configuration settings
├── leave_management.py       # Leave management module
├── performance_management.py # Performance evaluation module
├── reporting_functions.py    # Reporting and analytics module
├── requirements.txt          # Python dependencies
├── Procfile                  # For deployment (e.g., Heroku)
├── data/                     # Database and log files
│   ├── hr.db                # Main SQLite database
│   ├── hr_system.db         # Backup database
│   ├── db.sqlite3           # Legacy database
│   └── app.log              # Application logs
├── scripts/                  # Setup and utility scripts
│   ├── create_tables.py     # Create main tables
│   ├── create_leave_tables.py
│   ├── create_performance_tables.py
│   ├── create_reporting_tables.py
│   ├── init_db.py           # Initialize database with default data
│   ├── fake_emp.py          # Generate fake employee data
│   ├── fakeemp.py           # Generate fake employee data (alt)
│   ├── id_zero.py           # Reset employee IDs
│   ├── colom.py             # Column management utilities
│   └── serve.py             # Alternative server script
├── static/                   # Static assets
│   ├── images.jpg
│   ├── uploads/
│   └── employee_report.pdf
├── templates/               # Jinja2 HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── login.html
│   ├── employee_list.html
│   ├── add_employee.html
│   ├── edit_employee.html
│   ├── attendance.html
│   ├── leaves.html
│   ├── leave_balance.html
│   ├── my_leave_requests.html
│   ├── payroll.html
│   ├── add_payroll.html
│   ├── evaluate_employee.html
│   ├── evaluation_list.html
│   ├── evaluation_periods.html
│   ├── create_period.html
│   ├── employee_performance_history.html
│   ├── employees_with_evaluations/
│   ├── employee_details/
│   ├── leave_reports.html
│   └── employee_login.html
├── docs/                    # Documentation
│   ├── documentation.md
│   └── comprehensive_documentation.md
└── venv/                    # Python virtual environment
```

## Setup

1. Activate the virtual environment:
   ```bash
   source venv/Scripts/activate  # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Initialize the database:
   ```bash
   python scripts/init_db.py
   python scripts/create_tables.py
   python scripts/create_leave_tables.py
   python scripts/create_performance_tables.py
   python scripts/create_reporting_tables.py
   ```

4. (Optional) Generate fake employee data:
   ```bash
   python scripts/fake_emp.py
   ```

5. Run the application:
   ```bash
   python app.py
   ```

## Features

- Employee management (add, edit, list, details)
- Attendance tracking
- Leave management and balance tracking
- Performance evaluation with customizable criteria
- Payroll management
- PDF and Excel report generation
- Employee self-service portal
- Arabic language support

## Database

The main database is `data/hr.db`. Make sure this file exists and is accessible before running the application.
