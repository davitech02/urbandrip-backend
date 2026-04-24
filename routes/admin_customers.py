from flask import Blueprint, request, jsonify
from database import db
from models import User, Order
from app import admin_required
from sqlalchemy import func

admin_customers_bp = Blueprint('admin_customers', __name__)

@admin_customers_bp.route('', methods=['GET'])
@admin_required
def get_all_customers():
    """Get all registered users with stats"""
    try:
        users = User.query.all()
        
        customers = []
        for user in users:
            # Get order count and total spent
            orders = Order.query.filter_by(user_id=user.id).all()
            total_orders = len(orders)
            total_spent = sum(order.total_amount for order in orders if order.payment_status == 'successful')
            
            customers.append({
                'id': user.id,
                'full_name': user.full_name,
                'email': user.email,
                'phone': user.phone,
                'total_orders': total_orders,
                'total_spent': total_spent,
                'join_date': user.created_at.isoformat(),
                'is_active': user.is_active
            })
        
        return jsonify({
            'customers': customers
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_customers_bp.route('/<int:user_id>', methods=['GET'])
@admin_required
def get_customer(user_id):
    """Get a single customer with order history"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Customer not found'}), 404
        
        orders = Order.query.filter_by(user_id=user_id).all()
        total_spent = sum(order.total_amount for order in orders if order.payment_status == 'successful')
        
        return jsonify({
            'customer': {
                'id': user.id,
                'full_name': user.full_name,
                'email': user.email,
                'phone': user.phone,
                'total_orders': len(orders),
                'total_spent': total_spent,
                'join_date': user.created_at.isoformat(),
                'is_active': user.is_active,
                'orders': [order.to_dict() for order in orders]
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_customers_bp.route('/<int:user_id>/status', methods=['PUT'])
@admin_required
def toggle_customer_status(user_id):
    """Toggle customer active/inactive status"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Customer not found'}), 404
        
        user.is_active = not user.is_active
        db.session.commit()
        
        return jsonify({
            'message': 'Customer status updated',
            'is_active': user.is_active
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
