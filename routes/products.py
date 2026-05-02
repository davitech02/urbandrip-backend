from flask import Blueprint, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
from database import db
from models import Product
from decorators import admin_required
import os
import json
import time
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
        products = Product.query.filter_by(is_active=True).all()
        return jsonify({
            'products': [p.to_dict() for p in products],
            'total': len(products)
        }), 200
    except Exception as e:
        print(f"Get products error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@products_bp.route('/<int:id>', methods=['GET'])
def get_product(id):
    """Get single product details - public"""
    try:
        product = Product.query.get_or_404(id)
        
        if not product.is_active:
            return jsonify({'error': 'Product not found'}), 404
        
        return jsonify(product.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 404

# ============= ADMIN ENDPOINTS =============

@products_bp.route('/all', methods=['GET'])
@admin_required
def get_all_products():
    """Get all products (including inactive) - admin only"""
    try:
        products = Product.query.all()
        return jsonify([p.to_dict(include_inactive=True) for p in products]), 200
    except Exception as e:
        print(f"Get all products error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@products_bp.route('/create', methods=['POST'])
@admin_required
def create_product():
    """Create new product - admin only"""
    try:
        ensure_upload_folder()
        
        # Handle both JSON and FormData
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
            files = request.files
        else:
            data = request.get_json() or {}
            files = None

        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Product name is required'}), 400
        if not data.get('category'):
            return jsonify({'error': 'Category is required'}), 400
        if not data.get('price'):
            return jsonify({'error': 'Price is required'}), 400

        # Type conversions
        name = str(data.get('name', '')).strip()
        category = str(data.get('category', '')).strip()
        price = float(data.get('price', 0))
        
        original_price_raw = data.get('original_price')
        original_price = float(original_price_raw) if original_price_raw and original_price_raw != '' else None
        
        badge = str(data.get('badge')) if data.get('badge') and data.get('badge') != 'None' else None
        description = str(data.get('description', '')).strip()
        material = str(data.get('material', '')).strip() if data.get('material') else None
        care_instructions = str(data.get('care_instructions', '')).strip() if data.get('care_instructions') else None
        
        try:
            stock_quantity = int(data.get('stock_quantity', 0))
        except (ValueError, TypeError):
            stock_quantity = 0

        # Fix sizes — must be stored as JSON string in database
        sizes_raw = data.get('sizes', '[]')
        if isinstance(sizes_raw, str):
            try:
                sizes_list = json.loads(sizes_raw)
                sizes = json.dumps(sizes_list)
            except:
                sizes = json.dumps([])
        else:
            sizes = json.dumps(sizes_raw if isinstance(sizes_raw, list) else [])

        # Fix is_active boolean
        is_active_raw = data.get('is_active', True)
        if isinstance(is_active_raw, str):
            is_active = is_active_raw.lower() in ['true', '1', 'yes']
        else:
            is_active = bool(is_active_raw)

        # Handle image upload
        images_list = []
        if files and 'image' in files:
            file = files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = f"{int(time.time())}_{file.filename.replace(' ', '_')}"
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                image_url = f"http://localhost:5000/static/uploads/{filename}"
                images_list.append(image_url)
        elif data.get('image_url'):
            images_list.append(str(data.get('image_url')))
        
        images = json.dumps(images_list)

        # Create product
        new_product = Product(
            name=name,
            category=category,
            price=price,
            original_price=original_price,
            badge=badge,
            description=description,
            sizes=sizes,
            images=images,
            material=material,
            care_instructions=care_instructions,
            stock_quantity=stock_quantity,
            is_active=is_active
        )

        db.session.add(new_product)
        db.session.commit()

        return jsonify({
            'message': 'Product created successfully',
            'product': new_product.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Create product error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to create product: {str(e)}'}), 500

@products_bp.route('/<int:id>', methods=['PUT'])
@admin_required
def update_product(id):
    """Update product - admin only"""
    try:
        product = Product.query.get_or_404(id)
        ensure_upload_folder()
        
        # Handle both JSON and FormData
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
            files = request.files
        else:
            data = request.get_json() or {}
            files = None
        
        # Update string fields
        if data.get('name'):
            product.name = str(data.get('name')).strip()
        if data.get('category'):
            product.category = str(data.get('category')).strip()
        if data.get('description'):
            product.description = str(data.get('description')).strip()
        
        # Update numeric fields
        if data.get('price'):
            product.price = float(data.get('price'))
        if data.get('original_price'):
            product.original_price = float(data.get('original_price'))
        if data.get('stock_quantity'):
            product.stock_quantity = int(data.get('stock_quantity'))
        
        # Update optional string fields
        if data.get('badge'):
            product.badge = str(data.get('badge'))
        if data.get('material'):
            product.material = str(data.get('material')).strip()
        if data.get('care_instructions'):
            product.care_instructions = str(data.get('care_instructions')).strip()
        
        # Update sizes
        if data.get('sizes'):
            sizes_raw = data.get('sizes')
            if isinstance(sizes_raw, str):
                try:
                    sizes_list = json.loads(sizes_raw)
                    product.sizes = json.dumps(sizes_list)
                except:
                    product.sizes = json.dumps([])
            else:
                product.sizes = json.dumps(sizes_raw if isinstance(sizes_raw, list) else [])
        
        # Update is_active
        if 'is_active' in data:
            is_active_raw = data.get('is_active')
            if isinstance(is_active_raw, str):
                product.is_active = is_active_raw.lower() in ['true', '1', 'yes']
            else:
                product.is_active = bool(is_active_raw)
        
        # Handle new image upload
        if files and 'image' in files:
            file = files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = f"{int(time.time())}_{file.filename.replace(' ', '_')}"
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                image_url = f"http://localhost:5000/static/uploads/{filename}"
                images_list = json.loads(product.images) if product.images else []
                images_list.append(image_url)
                product.images = json.dumps(images_list)
        
        # Handle image URL
        if data.get('image_url'):
            images_list = json.loads(product.images) if product.images else []
            images_list.append(str(data.get('image_url')))
            product.images = json.dumps(images_list)
        
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Product updated successfully',
            'product': product.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Update product error: {str(e)}")
        return jsonify({'error': f'Failed to update product: {str(e)}'}), 500

@products_bp.route('/<int:id>', methods=['DELETE'])
@admin_required
def delete_product(id):
    """Soft delete product - admin only"""
    try:
        product = Product.query.get_or_404(id)
        product.is_active = False
        db.session.commit()
        
        return jsonify({'message': 'Product deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Delete product error: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
        
        filename = f"{int(time.time())}_{file.filename.replace(' ', '_')}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        image_url = f"http://localhost:5000/static/uploads/{filename}"
        
        return jsonify({
            'message': 'Image uploaded successfully',
            'image_url': image_url,
            'success': True
        }), 200
        
    except Exception as e:
        print(f"Upload image error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@products_bp.route('/../static/uploads/<filename>', methods=['GET'])
def serve_upload(filename):
    """Serve uploaded images"""
    try:
        return send_from_directory(UPLOAD_FOLDER, filename)
    except Exception as e:
        return jsonify({'error': 'File not found'}), 404