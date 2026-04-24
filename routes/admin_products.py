from flask import Blueprint, request, jsonify
from database import db
from models import Product
from app import admin_required
import os
from werkzeug.utils import secure_filename

admin_products_bp = Blueprint('admin_products', __name__)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_products_bp.route('', methods=['GET'])
@admin_required
def get_all_products():
    """Get all products including inactive (admin only)"""
    try:
        products = Product.query.all()
        
        return jsonify({
            'products': [product.to_dict(include_inactive=True) for product in products]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_products_bp.route('/<int:product_id>', methods=['GET'])
@admin_required
def get_product(product_id):
    """Get a single product"""
    try:
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        return jsonify({
            'product': product.to_dict(include_inactive=True)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_products_bp.route('', methods=['POST'])
@admin_required
def create_product():
    """Create a new product"""
    try:
        data = request.get_json()
        
        product = Product(
            name=data.get('name'),
            category=data.get('category'),
            price=data.get('price'),
            original_price=data.get('original_price'),
            badge=data.get('badge'),
            description=data.get('description'),
            sizes=data.get('sizes', []),
            stock_quantity=data.get('stock_quantity', 0),
            images=data.get('images', []),
            material=data.get('material'),
            care_instructions=data.get('care_instructions'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            'message': 'Product created',
            'product': product.to_dict(include_inactive=True)
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_products_bp.route('/<int:product_id>', methods=['PUT'])
@admin_required
def update_product(product_id):
    """Update a product"""
    try:
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            product.name = data['name']
        if 'category' in data:
            product.category = data['category']
        if 'price' in data:
            product.price = data['price']
        if 'original_price' in data:
            product.original_price = data['original_price']
        if 'badge' in data:
            product.badge = data['badge']
        if 'description' in data:
            product.description = data['description']
        if 'sizes' in data:
            product.sizes = data['sizes']
        if 'stock_quantity' in data:
            product.stock_quantity = data['stock_quantity']
        if 'images' in data:
            product.images = data['images']
        if 'material' in data:
            product.material = data['material']
        if 'care_instructions' in data:
            product.care_instructions = data['care_instructions']
        if 'is_active' in data:
            product.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Product updated',
            'product': product.to_dict(include_inactive=True)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_products_bp.route('/<int:product_id>', methods=['DELETE'])
@admin_required
def delete_product(product_id):
    """Delete a product"""
    try:
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({'message': 'Product deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_products_bp.route('/upload-image', methods=['POST'])
@admin_required
def upload_image():
    """Upload a product image"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Create upload folder if it doesn't exist
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Save file
        filename = secure_filename(file.filename)
        import uuid
        filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Return URL
        image_url = f"/static/uploads/{filename}"
        
        return jsonify({
            'message': 'Image uploaded',
            'image_url': image_url
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
