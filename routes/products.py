from flask import Blueprint, jsonify, request
from database import db
from models import Product

products_bp = Blueprint('products', __name__)

# Get all products
@products_bp.route('/', methods=['GET'])
def get_products():
    category = request.args.get('category')
    if category:
        products = Product.query.filter_by(category=category).all()
    else:
        products = Product.query.all()
    
    output = []
    for p in products:
        output.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "image_url": p.image_url,
            "stock": p.stock,
            "category": p.category
            
        })
    return jsonify(output)

# Get single product details
@products_bp.route('/<int:id>', methods=['GET'])
def get_product(id):
    p = Product.query.get_or_404(id)
    return jsonify({
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "price": p.price,
        "image_url": p.image_url,
        "stock": p.stock,
        "category": p.category,
        "sizes": p.sizes
        
    })