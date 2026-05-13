from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from functools import wraps

# Admin required decorator
def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception as e:
            print(f"[AUTH] JWT verification failed: {str(e)}")
            return jsonify({'error': f'Authorization failed: {str(e)}'}), 401
        
        try:
            from models import User
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            if not user or user.role != 'admin':
                print(f"[AUTH] User not admin - user_id: {user_id}, role: {user.role if user else 'None'}")
                return jsonify({'error': 'Admin access required'}), 403
            return fn(*args, **kwargs)
        except Exception as e:
            print(f"[AUTH] Admin check failed: {str(e)}")
            return jsonify({'error': str(e)}), 500
    return wrapper
