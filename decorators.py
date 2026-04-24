from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from functools import wraps

# Admin required decorator
def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        from models import User
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return fn(*args, **kwargs)
    return wrapper
