from database import db
from datetime import datetime
import json

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'user' or 'admin'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    def make_admin(self):
        """Make this user an admin"""
        self.role = 'admin'
        db.session.commit()

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'created_at': self.created_at.isoformat()
        }

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    original_price = db.Column(db.Float, nullable=True)
    badge = db.Column(db.String(50), nullable=True)  # 'NEW', 'SALE', or None
    description = db.Column(db.Text, nullable=True)
    sizes = db.Column(db.Text, default='[]')  # JSON array stored as string
    stock_quantity = db.Column(db.Integer, default=0)
    images = db.Column(db.Text, default='[]')  # JSON array stored as string
    material = db.Column(db.String(200), nullable=True)
    care_instructions = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, include_inactive=False):
        if not self.is_active and not include_inactive:
            return None
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'price': self.price,
            'original_price': self.original_price,
            'badge': self.badge,
            'description': self.description,
            'sizes': json.loads(self.sizes) if isinstance(self.sizes, str) else self.sizes or [],
            'stock_quantity': self.stock_quantity,
            'images': json.loads(self.images) if isinstance(self.images, str) else self.images or [],
            'material': self.material,
            'care_instructions': self.care_instructions,
            'is_active': bool(self.is_active),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Customer Info
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    
    # Order Details
    delivery_address = db.Column(db.JSON, nullable=False)
    items = db.Column(db.JSON, nullable=False)
    
    # Pricing
    subtotal = db.Column(db.Float, nullable=False)
    shipping_fee = db.Column(db.Float, default=0)
    discount = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, nullable=False)
    
    # Payment & Delivery
    delivery_method = db.Column(db.String(50), default='standard')
    tx_ref = db.Column(db.String(100), unique=True, nullable=True)
    flutterwave_ref = db.Column(db.String(100), nullable=True)
    
    # Status
    payment_status = db.Column(db.String(50), default='pending')
    order_status = db.Column(db.String(50), default='processing')
    
    # Tracking History
    tracking_history = db.Column(db.JSON, default=list)  # Array of {status, note, timestamp}
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def add_tracking_entry(self, status, note=''):
        """Add a tracking history entry"""
        entry = {
            'status': status,
            'note': note,
            'timestamp': datetime.utcnow().isoformat()
        }
        if not self.tracking_history:
            self.tracking_history = []
        self.tracking_history.append(entry)
        self.order_status = status
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def to_dict(self):
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'customer_email': self.customer_email,
            'customer_phone': self.customer_phone,
            'total_amount': self.total_amount,
            'payment_status': self.payment_status,
            'order_status': self.order_status,
            'delivery_method': self.delivery_method,
            'tx_ref': self.tx_ref,
            'items': self.items,
            'delivery_address': self.delivery_address,
            'tracking_history': self.tracking_history,
            'created_at': self.created_at.isoformat()
        }

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

class Visitor(db.Model):
    __tablename__ = 'visitors'
    
    id = db.Column(db.Integer, primary_key=True)
    visitor_id = db.Column(db.String(100), nullable=False)  # UUID for unique visitor
    page_url = db.Column(db.String(500), nullable=False)
    referrer = db.Column(db.String(500), nullable=True)
    device_type = db.Column(db.String(50), nullable=True)  # 'mobile' or 'desktop'
    browser = db.Column(db.String(200), nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'visitor_id': self.visitor_id,
            'page_url': self.page_url,
            'device_type': self.device_type,
            'browser': self.browser,
            'timestamp': self.timestamp.isoformat()
        }

class Settings(db.Model):
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_setting(key, default=None):
        """Get a setting by key"""
        setting = Settings.query.filter_by(key=key).first()
        return setting.value if setting else default

    @staticmethod
    def set_setting(key, value):
        """Set a setting by key"""
        setting = Settings.query.filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            setting = Settings(key=key, value=value)
            db.session.add(setting)
        db.session.commit()
        return setting

class DiscountCode(db.Model):
    __tablename__ = 'discount_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_percentage = db.Column(db.Float, nullable=False)
    expiry_date = db.Column(db.DateTime, nullable=True)
    usage_count = db.Column(db.Integer, default=0)
    max_usage = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_valid(self):
        """Check if discount code is still valid"""
        if not self.is_active:
            return False
        if self.expiry_date and datetime.utcnow() > self.expiry_date:
            return False
        if self.max_usage and self.usage_count >= self.max_usage:
            return False
        return True

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'discount_percentage': self.discount_percentage,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'usage_count': self.usage_count,
            'max_usage': self.max_usage,
            'is_active': self.is_active
        }

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin_reply = db.Column(db.Boolean, default=False)