from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db
from models import Order, OrderItem, Product
from app import admin_required
import json
from datetime import datetime

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/create', methods=['POST'])
def create_order_guest():
    """Create order for guest or authenticated user - no auth required"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Extract delivery address
        delivery_address = json.dumps(data.get('delivery_address', {}))
        
        # Extract items
        items_json = json.dumps(data.get('items', []))
        
        new_order = Order(
            user_id=None,  # Guest checkout
            customer_name=data.get('customer_name'),
            customer_email=data.get('customer_email'),
            customer_phone=data.get('customer_phone'),
            delivery_address=delivery_address,
            items=items_json,
            subtotal=data.get('subtotal', 0),
            shipping_fee=data.get('shipping_fee', 0),
            discount=data.get('discount', 0),
            total_amount=data.get('total_amount', 0),
            delivery_method=data.get('delivery_method', 'standard'),
            tx_ref=data.get('tx_ref'),
            flutterwave_ref=data.get('flutterwave_ref'),
            payment_status=data.get('payment_status', 'pending'),
            order_status='processing'
        )
        
        db.session.add(new_order)
        db.session.commit()
        
        return jsonify({
            'message': 'Order created successfully',
            'order_id': new_order.id,
            'tx_ref': new_order.tx_ref
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating order: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@orders_bp.route('/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get single order by ID"""
    try:
        order = Order.query.get(order_id)

        if not order:
            return jsonify({'error': 'Order not found'}), 404

        items = json.loads(order.items) if order.items else []
        delivery_address = json.loads(order.delivery_address) if order.delivery_address else {}

        return jsonify({
            'order': {
                'id': order.id,
                'customer_name': order.customer_name,
                'customer_email': order.customer_email,
                'customer_phone': order.customer_phone,
                'total_amount': order.total_amount,
                'payment_status': order.payment_status,
                'order_status': order.order_status,
                'delivery_method': order.delivery_method,
                'tx_ref': order.tx_ref,
                'items': items,
                'delivery_address': delivery_address,
                'created_at': order.created_at.isoformat()
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@orders_bp.route('/track/<tx_ref>', methods=['GET'])
def track_order(tx_ref):
    """Get order by transaction reference"""
    try:
        order = Order.query.filter_by(tx_ref=tx_ref).first()

        if not order:
            return jsonify({'error': 'Order not found'}), 404

        items = json.loads(order.items) if order.items else []
        delivery_address = json.loads(order.delivery_address) if order.delivery_address else {}

        return jsonify({
            'order': {
                'id': order.id,
                'tx_ref': order.tx_ref,
                'customer_name': order.customer_name,
                'customer_email': order.customer_email,
                'customer_phone': order.customer_phone,
                'total_amount': order.total_amount,
                'payment_status': order.payment_status,
                'order_status': order.order_status,
                'delivery_method': order.delivery_method,
                'items': items,
                'delivery_address': delivery_address,
                'created_at': order.created_at.isoformat(),
                'updated_at': order.updated_at.isoformat() if order.updated_at else None
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@orders_bp.route('/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_orders(user_id):
    """Get all orders for authenticated user"""
    try:
        current_user = get_jwt_identity()

        # Only allow users to view their own orders
        if int(current_user) != user_id:
            return jsonify({'error': 'Unauthorized'}), 403

        orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()

        output = []
        for order in orders:
            items = json.loads(order.items) if order.items else []
            delivery_address = json.loads(order.delivery_address) if order.delivery_address else {}

            output.append({
                'id': order.id,
                'tx_ref': order.tx_ref,
                'customer_name': order.customer_name,
                'customer_email': order.customer_email,
                'customer_phone': order.customer_phone,
                'total_amount': order.total_amount,
                'payment_status': order.payment_status,
                'order_status': order.order_status,
                'delivery_method': order.delivery_method,
                'items': items,
                'delivery_address': delivery_address,
                'created_at': order.created_at.isoformat(),
                'updated_at': order.updated_at.isoformat() if order.updated_at else None
            })

        return jsonify({'orders': output}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@orders_bp.route('/<int:order_id>/status', methods=['PUT'])
@admin_required
def admin_update_order_status(order_id):
    """Update order status with tracking history (admin only)"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        tracking_note = data.get('tracking_note', '')

        if not new_status:
            return jsonify({'error': 'Status is required'}), 400

        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404

        # Add tracking entry
        order.add_tracking_entry(new_status, tracking_note)

        return jsonify({
            'message': 'Order status updated successfully',
            'order': order.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/admin/all', methods=['GET'])
@admin_required
def get_all_orders():
    """Get all orders (admin only)"""
    try:
        status_filter = request.args.get('status')
        
        query = Order.query.order_by(Order.created_at.desc())
        
        if status_filter:
            query = query.filter_by(order_status=status_filter)
        
        orders = query.all()
        
        return jsonify({
            'orders': [order.to_dict() for order in orders]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/<int:order_id>', methods=['GET'])
@admin_required
def admin_get_order_details(order_id):
    """Get detailed order information (admin only)"""
    try:
        order = Order.query.get(order_id)

        if not order:
            return jsonify({'error': 'Order not found'}), 404

        return jsonify({
            'order': order.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500