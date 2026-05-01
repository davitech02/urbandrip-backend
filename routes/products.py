from flask import Blueprint, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
from database import db
from models import Product
from decorators import admin_required
import os
from datetime import datetime

products_bp = Blueprint('products', __name__)

# Allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
UPLOAD_FOLDER = 'static/uploads'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_folder():
    """Ensure uploads folder exists"""
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ============= PUBLIC ENDPOINTS =============

@products_bp.route('/', methods=['GET'])
def get_products():
    """Get all active products - public endpoint"""
    try:
        category = request.args.get('category')
        
        query = Product.query.filter_by(is_active=True)
        
        if category:
            query = query.filter_by(category=category)
        
        products = query.all()
        
        return jsonify({
            'success': True,
            'products': [p.to_dict() for p in products]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/<int:id>', methods=['GET'])
def get_product(id):
    """Get single product details - public"""
    try:
        product = Product.query.get_or_404(id)
        
        if not product.is_active:
            return jsonify({'error': 'Product not found'}), 404
        
        return jsonify({
            'success': True,
            'product': product.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 404

# ============= ADMIN ENDPOINTS =============

@products_bp.route('/all', methods=['GET'])
@admin_required
def get_all_products():
    """Get all products (including inactive) - admin only"""
    try:
        products = Product.query.all()
        
        return jsonify({
            'success': True,
            'products': [p.to_dict(include_inactive=True) for p in products]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/create', methods=['POST'])
@admin_required
def create_product():
    """Create new product - admin only"""
    try:
        ensure_upload_folder()
        
        # Handle both JSON and FormData
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Validate required fields
        required_fields = ['name', 'category', 'price', 'description']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        try:
            price = float(data.get('price', 0))
            if price <= 0:
                return jsonify({'error': 'Price must be greater than 0'}), 400
        except ValueError:
            return jsonify({'error': 'Price must be a valid number'}), 400
        
        # Handle stock quantity
        try:
            stock_quantity = int(data.get('stock_quantity', 0))
        except ValueError:
            stock_quantity = 0
        
        # Handle images
        images = []
        
        # Image from URL in form data
        if data.get('image_url'):
            images.append(data.get('image_url'))
        
        # Image file upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                # Create URL based on environment
                image_url = f"{os.getenv('BACKEND_URL', 'http://localhost:5000')}/static/uploads/{filename}"
                images.append(image_url)
        
        # Handle sizes
        sizes = data.get('sizes', [])
        if isinstance(sizes, str):
            try:
                import json
                sizes = json.loads(sizes)
            except:
                sizes = [sizes]
        
        # Create product
        product = Product(
            name=data.get('name'),
            category=data.get('category'),
            price=price,
            original_price=data.get('original_price'),
            badge=data.get('badge'),
            description=data.get('description'),
            sizes=sizes if isinstance(sizes, list) else [],
            stock_quantity=stock_quantity,
            images=images,
            material=data.get('material'),
            care_instructions=data.get('care_instructions'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product created successfully',
            'product': product.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/<int:id>', methods=['PUT'])
@admin_required
def update_product(id):
    """Update product - admin only"""
    try:
        product = Product.query.get_or_404(id)
        ensure_upload_folder()
        
        # Handle both JSON and FormData
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Update fields
        if data.get('name'):
            product.name = data.get('name')
        if data.get('category'):
            product.category = data.get('category')
        if data.get('price'):
            product.price = float(data.get('price'))
        if data.get('original_price'):
            product.original_price = float(data.get('original_price'))
        if data.get('badge') is not None:
            product.badge = data.get('badge')
        if data.get('description'):
            product.description = data.get('description')
        if data.get('material') is not None:
            product.material = data.get('material')
        if data.get('care_instructions') is not None:
            product.care_instructions = data.get('care_instructions')
        if 'is_active' in data:
            product.is_active = data.get('is_active') in [True, 'true', '1', 'True']
        
        # Handle stock_quantity
        if data.get('stock_quantity'):
            product.stock_quantity = int(data.get('stock_quantity'))
        
        # Handle sizes
        if data.get('sizes'):
            sizes = data.get('sizes')
            if isinstance(sizes, str):
                try:
                    import json
                    sizes = json.loads(sizes)
                except:
                    sizes = [sizes]
            product.sizes = sizes if isinstance(sizes, list) else []
        
        # Handle new image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                image_url = f"{os.getenv('BACKEND_URL', 'http://localhost:5000')}/static/uploads/{filename}"
                if not product.images:
                    product.images = []
                product.images.append(image_url)
        
        # Handle image URL
        if data.get('image_url'):
            if not product.images:
                product.images = []
            product.images.append(data.get('image_url'))
        
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product updated successfully',
            'product': product.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/<int:id>', methods=['DELETE'])
@admin_required
def delete_product(id):
    """Soft delete product - admin only"""
    try:
        product = Product.query.get_or_404(id)
        
        # Soft delete
        product.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@products_bp.route('/upload-image', methods=['POST'])
@admin_required
def upload_image():
    """Upload product image - admin only"""
    try:
        ensure_upload_folder()
        
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        
        if not file or not file.filename:
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Use PNG, JPG, JPEG, GIF, or WEBP'}), 400
        
        filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Return the full image URL
        image_url = f"{os.getenv('BACKEND_URL', 'http://localhost:5000')}/static/uploads/{filename}"
        
        return jsonify({
            'success': True,
            'message': 'Image uploaded successfully',
            'image_url': image_url
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Serve uploaded files
@products_bp.route('/../static/uploads/<filename>', methods=['GET'])
def serve_upload(filename):
    """Serve uploaded images"""
    try:
        return send_from_directory(UPLOAD_FOLDER, filename)
    except Exception as e:
        return jsonify({'error': 'File not found'}), 404