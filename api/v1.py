"""API v1 Blueprint for HR System."""
from flask import Blueprint
from flask_restx import Api

# Create the blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Initialize Flask-RESTX API
api = Api(
    api_bp,
    version='1.0',
    title='HR System API',
    description='''RESTful API for HR Management System

    Features:
    - Employee management (CRUD operations)
    - Leave request handling
    - Performance evaluation tracking
    - Report generation
    - Webhook support for third-party integrations

    Authentication:
    - Currently using session-based auth from the main application
    - Future versions will implement JWT/OAuth2

    Rate Limiting:
    - 100 requests per minute per IP (planned)
    ''',
    doc='/docs/',  # Swagger UI will be available at /api/v1/docs/
    authorizations={
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': "Add 'Bearer <JWT>' to authorize"
        }
    },
    security='Bearer'
)

# Import and register API namespaces
from . import employees
employees.register_namespace(api)

# Additional namespaces will be added as they are created
# from . import leaves, performance, reports, auth
# api.add_namespace(leaves.ns, path='/leaves')
# api.add_namespace(performance.ns, path='/performance')
# api.add_namespace(reports.ns, path='/reports')
# api.add_namespace(auth.ns, path='/auth')