from flask import Blueprint, request, jsonify
from database import db
from models import Settings, DiscountCode
from decorators import admin_required

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/admin/settings', methods=['GET'])
@admin_required
def get_settings():
    """Get all settings"""
    try:
        settings = Settings.query.all()
        
        settings_dict = {}
        for setting in settings:
            settings_dict[setting.key] = setting.value
        
        return jsonify(settings_dict), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/admin/settings', methods=['PUT'])
@admin_required
def update_settings():
    """Update settings"""
    try:
        data = request.get_json()
        
        for key, value in data.items():
            Settings.set_setting(key, value)
        
        return jsonify({'message': 'Settings updated'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/admin/discount-codes', methods=['GET'])
@admin_required
def get_discount_codes():
    """Get all discount codes"""
    try:
        codes = DiscountCode.query.all()
        
        return jsonify({
            'codes': [code.to_dict() for code in codes]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/admin/discount-codes', methods=['POST'])
@admin_required
def create_discount_code():
    """Create a new discount code"""
    try:
        data = request.get_json()
        
        # Check if code already exists
        existing = DiscountCode.query.filter_by(code=data.get('code')).first()
        if existing:
            return jsonify({'error': 'Discount code already exists'}), 400
        
        code = DiscountCode(
            code=data.get('code').upper(),
            discount_percentage=data.get('discount_percentage'),
            expiry_date=data.get('expiry_date'),
            max_usage=data.get('max_usage'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(code)
        db.session.commit()
        
        return jsonify({
            'message': 'Discount code created',
            'code': code.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/admin/discount-codes/<code_id>', methods=['DELETE'])
@admin_required
def delete_discount_code(code_id):
    """Delete a discount code"""
    try:
        code = DiscountCode.query.get(code_id)
        
        if not code:
            return jsonify({'error': 'Discount code not found'}), 404
        
        db.session.delete(code)
        db.session.commit()
        
        return jsonify({'message': 'Discount code deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Public route to validate discount code
@settings_bp.route('/validate-discount/<code>', methods=['GET'])
def validate_discount(code):
    """Validate a discount code"""
    try:
        code_obj = DiscountCode.query.filter_by(code=code.upper()).first()
        
        if not code_obj or not code_obj.is_valid():
            return jsonify({'valid': False}), 404
        
        return jsonify({
            'valid': True,
            'discount_percentage': code_obj.discount_percentage
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
