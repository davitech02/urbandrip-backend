from flask import Flask, jsonify, request, send_from_directory
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
    
    # Ensure uploads folder exists
    os.makedirs('static/uploads', exist_ok=True)

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
    from routes.admin_customers import admin_customers_bp
    from routes.admin_products import admin_products_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(orders_bp, url_prefix='/api/orders')
    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(visitors_bp, url_prefix='/api/visitors')
    app.register_blueprint(settings_bp, url_prefix='/api')
    app.register_blueprint(admin_customers_bp, url_prefix='/api/admin/customers')
    app.register_blueprint(admin_products_bp, url_prefix='/api/admin/products')

    # Import models to ensure they are registered with SQLAlchemy
    from models import User, Product, Order, Visitor, Settings, DiscountCode

    @app.before_request
    def handle_options():
        if request.method == 'OPTIONS':
            return jsonify({}), 200

    # Error handlers - ensure all responses are JSON
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request', 'details': str(error)}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized', 'details': str(error)}), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden', 'details': str(error)}), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found', 'details': str(error)}), 404

    @app.errorhandler(500)
    def internal_error(error):
        print(f"Internal server error: {str(error)}")
        return jsonify({'error': 'Internal server error', 'details': str(error)}), 500

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

    # Serve uploaded files
    @app.route('/static/uploads/<filename>', methods=['GET'])
    def serve_upload(filename):
        try:
            return send_from_directory('static/uploads', filename)
        except Exception as e:
            return jsonify({'error': 'File not found'}), 404

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

    # Admin dashboard stats aggregation route
    @app.route('/api/admin/stats', methods=['GET'])
    @admin_required
    def get_admin_stats():
        """Get aggregated admin dashboard statistics"""
        try:
            from datetime import datetime, timedelta
            from sqlalchemy import func
            
            # Get total products (active and inactive)
            total_products = Product.query.count()
            active_products = Product.query.filter_by(is_active=True).count()
            
            # Get orders stats
            total_orders = Order.query.count()
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            orders_today = Order.query.filter(Order.created_at >= today).count()
            
            # Get revenue stats
            successful_orders = Order.query.filter_by(payment_status='successful').all()
            total_revenue = sum(order.total_amount for order in successful_orders)
            revenue_today = sum(order.total_amount for order in successful_orders if order.created_at >= today)
            
            # Get customer stats
            total_customers = User.query.filter(User.role != 'admin').count()
            
            # Get visitor stats
            total_visitors = Visitor.query.count()
            visitors_today = Visitor.query.filter(Visitor.timestamp >= today).count()
            
            return jsonify({
                'products': {
                    'total': total_products,
                    'active': active_products,
                    'inactive': total_products - active_products
                },
                'orders': {
                    'total': total_orders,
                    'today': orders_today
                },
                'revenue': {
                    'total': round(total_revenue, 2),
                    'today': round(revenue_today, 2)
                },
                'customers': {
                    'total': total_customers
                },
                'visitors': {
                    'total': total_visitors,
                    'today': visitors_today
                }
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Create all tables
    with app.app_context():
        db.create_all()
        print("Database tables created successfully")
        
        # Ensure admin user exists
        admin_user = User.query.filter_by(email="theadmin@gmail.com").first()
        if not admin_user:
            hashed_password = bcrypt.generate_password_hash("admin1234").decode('utf-8')
            admin_user = User(
                full_name="ADMIN",
                email="theadmin@gmail.com",
                phone="08000000000",
                password_hash=hashed_password,
                role="admin",
                is_active=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Admin user created successfully")
            print(f"📧 Email: theadmin@gmail.com")
            print(f"🔑 Password: admin1234")
        else:
            # Ensure admin has admin role
            if admin_user.role != 'admin':
                admin_user.role = 'admin'
                db.session.commit()
                print("✅ Admin role updated")

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

