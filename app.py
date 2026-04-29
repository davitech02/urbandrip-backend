from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from database import db, bcrypt, jwt
from decorators import admin_required
import os
import re

def create_app():
    app = Flask(__name__)

    # Config
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urbandrip.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'urbandrip-secret-key-2024'
    app.config['SECRET_KEY'] = 'urbandrip-flask-secret'

    # CORS - Allow localhost and any Vercel deployment
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5176",
        "http://localhost:5177",
        "http://127.0.0.1:5177",
        "https://urbandrip-app.vercel.app",
        r"https://.*\.vercel\.app",  # Allow any Vercel deployment
    ]

    def cors_origin_matcher(origin):
        """Check if origin matches allowed patterns"""
        if origin in allowed_origins:
            return True
        # Check regex patterns
        for pattern in allowed_origins:
            if pattern.startswith('r"') and pattern.endswith('"'):
                regex_pattern = pattern[2:-1]
                if re.match(regex_pattern, origin or ""):
                    return True
        return False

    CORS(app, resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "max_age": 3600
        }
    })

    # Init extensions
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.orders import orders_bp
    from routes.products import products_bp
    from routes.visitors import visitors_bp
    from routes.settings import settings_bp
    from routes.admin_products import admin_products_bp
    from routes.admin_customers import admin_customers_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(orders_bp, url_prefix='/api/orders')
    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(visitors_bp, url_prefix='/api/visitors')
    app.register_blueprint(settings_bp, url_prefix='/api')
    app.register_blueprint(admin_products_bp, url_prefix='/api/admin/products')
    app.register_blueprint(admin_customers_bp, url_prefix='/api/admin/customers')

    # Import models to ensure they are registered with SQLAlchemy
    from models import User, Product, Order, Visitor, Settings, DiscountCode

    @app.before_request
    def handle_options():
        if request.method == 'OPTIONS':
            return jsonify({}), 200

    # Health check route
    @app.route('/api/health', methods=['GET'])
    def health():
        try:
            db.session.execute(db.text('SELECT 1'))
            return jsonify({
                'status': 'ok',
                'database': 'connected',
                'message': 'Urban Drip API is running'
            }), 200
        except Exception as e:
            return jsonify({'status': 'error', 'database': str(e)}), 500

    # Verify admin user route (temporary for testing)
    @app.route('/api/admin/verify', methods=['GET'])
    def verify_admin():
        admin_user = User.query.filter_by(email="theadmin@gmail.com").first()
        if admin_user:
            return jsonify({
                'id': admin_user.id,
                'full_name': admin_user.full_name,
                'email': admin_user.email,
                'role': admin_user.role,
                'exists': True
            }), 200
        else:
            return jsonify({
                'exists': False,
                'message': 'Admin user not found'
            }), 404

    # Create all tables
    with app.app_context():
        db.create_all()
        print("Database tables created successfully")

    # CLI Commands
    @app.cli.command()
    def make_admin():
        """Make a user an admin by email"""
        import sys
        if len(sys.argv) < 2:
            print("Usage: flask make-admin <email>")
            return
        
        email = sys.argv[1]
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"User with email {email} not found")
            return
        
        user.make_admin()
        print(f"Success: {email} is now an admin")

    return app

# This is needed for gunicorn deployment
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')

