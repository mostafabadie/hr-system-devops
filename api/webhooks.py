"""Webhook support for third-party integrations."""
from flask import Blueprint, request, jsonify, current_app
import hmac
import hashlib
import json
import logging
from functools import wraps

# Create blueprint
webhooks_bp = Blueprint('webhooks', __name__, url_prefix='/webhooks')


def get_webhook_secret():
    return current_app.config.get(
        'WEBHOOK_SECRET',
        'your-webhook-secret-key'
    )


def verify_webhook_signature(f):
    """Decorator to verify webhook signature."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        signature = request.headers.get('X-Hub-Signature-256')

        if not signature:
            return jsonify({'error': 'Missing signature'}), 401

        # Get raw request data
        data = request.get_data()

        # Get secret داخل الـ app context
        webhook_secret = get_webhook_secret()

        # Calculate expected signature
        expected_signature = 'sha256=' + hmac.new(
            webhook_secret.encode('utf-8'),
            data,
            hashlib.sha256
        ).hexdigest()

        # Compare signatures
        if not hmac.compare_digest(signature, expected_signature):
            return jsonify({'error': 'Invalid signature'}), 401

        return f(*args, **kwargs)

    return decorated_function

@webhooks_bp.route('/employee/created', methods=['POST'])
@verify_webhook_signature
def employee_created():
    """Handle employee created webhook from external systems."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        # Process employee data (this would typically integrate with your employee creation logic)
        employee_data = {
            'external_id': data.get('id'),
            'name': data.get('name'),
            'email': data.get('email'),
            'department': data.get('department'),
            'position': data.get('position')
        }

        # Log the webhook receipt
        current_app.logger.info(f"Received employee created webhook: {employee_data}")

        # Here you would typically:
        # 1. Validate the data
        # 2. Check if employee already exists
        # 3. Create or update employee in your system
        # 4. Return appropriate response

        return jsonify({
            'status': 'success',
            'message': 'Employee webhook processed',
            'data': employee_data
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error processing employee webhook: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@webhooks_bp.route('/leave/requested', methods=['POST'])
@verify_webhook_signature
def leave_requested():
    """Handle leave requested webhook from external systems."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        # Process leave request data
        leave_data = {
            'external_id': data.get('id'),
            'employee_id': data.get('employee_id'),
            'start_date': data.get('start_date'),
            'end_date': data.get('end_date'),
            'leave_type': data.get('leave_type'),
            'reason': data.get('reason')
        }

        # Log the webhook receipt
        current_app.logger.info(f"Received leave requested webhook: {leave_data}")

        # Here you would typically:
        # 1. Validate the data
        # 2. Check if employee exists
        # 3. Create leave request in your system
        # 4. Return appropriate response

        return jsonify({
            'status': 'success',
            'message': 'Leave request webhook processed',
            'data': leave_data
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error processing leave webhook: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@webhooks_bp.route('/performance/completed', methods=['POST'])
@verify_webhook_signature
def performance_completed():
    """Handle performance evaluation completed webhook from external systems."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        # Process performance data
        performance_data = {
            'external_id': data.get('id'),
            'employee_id': data.get('employee_id'),
            'period_id': data.get('period_id'),
            'score': data.get('score'),
            'rating': data.get('rating'),
            'comments': data.get('comments')
        }

        # Log the webhook receipt
        current_app.logger.info(f"Received performance completed webhook: {performance_data}")

        # Here you would typically:
        # 1. Validate the data
        # 2. Check if employee and period exist
        # 3. Update or create performance evaluation in your system
        # 4. Return appropriate response

        return jsonify({
            'status': 'success',
            'message': 'Performance webhook processed',
            'data': performance_data
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error processing performance webhook: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Health check endpoint for webhooks
@webhooks_bp.route('/health', methods=['GET'])
def webhook_health():
    """Health check for webhook service."""
    return jsonify({
        'status': 'healthy',
        'service': 'webhooks',
        'timestamp': request.environ.get('REQUEST_TIME')
    }), 200