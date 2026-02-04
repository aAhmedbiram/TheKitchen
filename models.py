from datetime import datetime
from extensions import db
from flask_login import UserMixin
import json


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='user', lazy=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    
    id = db.Column(db.Integer, primary_key=True)
    name_ar = db.Column(db.String(200), nullable=False)
    name_en = db.Column(db.String(200), nullable=False)
    description_ar = db.Column(db.Text, nullable=False)
    description_en = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    image_urls = db.Column(db.Text)  # JSON array of image URLs
    category = db.Column(db.String(100), default='main')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='menu_item', lazy=True)
    
    def get_image_urls(self):
        """Parse image URLs from JSON string"""
        if self.image_urls:
            try:
                return json.loads(self.image_urls)
            except:
                return []
        return []
    
    def set_image_urls(self, urls):
        """Set image URLs as JSON string"""
        self.image_urls = json.dumps(urls) if urls else '[]'
    
    def get_name(self, language='en'):
        """Get name based on language"""
        return self.name_ar if language == 'ar' else self.name_en
    
    def get_description(self, language='en'):
        """Get description based on language"""
        return self.description_ar if language == 'ar' else self.description_en
    
    def to_dict(self, language='en'):
        return {
            "id": self.id,
            "name": self.get_name(language),
            "name_ar": self.name_ar,
            "name_en": self.name_en,
            "description": self.get_description(language),
            "description_ar": self.description_ar,
            "description_en": self.description_en,
            "price": float(self.price),
            "is_available": self.is_available,
            "image_urls": self.get_image_urls(),
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(50), default='new')  # new, confirmed, preparing, on_way, delivered, cancelled
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    delivery_fee = db.Column(db.Numeric(10, 2), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    advance_amount = db.Column(db.Numeric(10, 2), nullable=False)
    delivery_address = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text)  # Customer notes
    admin_notes = db.Column(db.Text)  # Internal admin notes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='order', lazy=True)
    
    def get_status_display(self, language='en'):
        """Get status display text based on language"""
        status_map = {
            'new': {'en': 'New', 'ar': 'جديد'},
            'confirmed': {'en': 'Confirmed', 'ar': 'مؤكد'},
            'preparing': {'en': 'Preparing', 'ar': 'قيد التحضير'},
            'on_way': {'en': 'On the way', 'ar': 'في الطريق'},
            'delivered': {'en': 'Delivered', 'ar': 'تم التسليم'},
            'cancelled': {'en': 'Cancelled', 'ar': 'ملغي'}
        }
        return status_map.get(self.status, {}).get(language, self.status)
    
    def to_dict(self, language='en'):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status,
            "status_display": self.get_status_display(language),
            "subtotal": float(self.subtotal),
            "delivery_fee": float(self.delivery_fee),
            "total_amount": float(self.total_amount),
            "advance_amount": float(self.advance_amount),
            "delivery_address": self.delivery_address,
            "notes": self.notes,
            "admin_notes": self.admin_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "items": [item.to_dict(language) for item in self.items],
            "payments": [payment.to_dict() for payment in self.payments]
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    notes = db.Column(db.Text)  # Item-specific notes (e.g., "no onion")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self, language='en'):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "menu_item_id": self.menu_item_id,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price),
            "total_price": float(self.unit_price * self.quantity),
            "notes": self.notes,
            "menu_item": self.menu_item.to_dict(language) if self.menu_item else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    method = db.Column(db.String(50), nullable=False)  # instapay, vodafone_cash, orange_money, etisalat_wallet, cod
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, rejected
    screenshot_url = db.Column(db.String(255))  # Payment proof screenshot
    transaction_id = db.Column(db.String(100))  # Transaction reference
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_method_display(self, language='en'):
        """Get payment method display text based on language"""
        method_map = {
            'instapay': {'en': 'Instapay', 'ar': 'إنستاباي'},
            'vodafone_cash': {'en': 'Vodafone Cash', 'ar': 'فودافون كاش'},
            'orange_money': {'en': 'Orange Money', 'ar': 'أورانج موني'},
            'etisalat_wallet': {'en': 'Etisalat Wallet', 'ar': 'محفظة اتصالات'},
            'cod': {'en': 'Cash on Delivery', 'ar': 'الدفع عند الاستلام'}
        }
        return method_map.get(self.method, {}).get(language, self.method)
    
    def get_status_display(self, language='en'):
        """Get status display text based on language"""
        status_map = {
            'pending': {'en': 'Pending', 'ar': 'في الانتظار'},
            'confirmed': {'en': 'Confirmed', 'ar': 'مؤكد'},
            'rejected': {'en': 'Rejected', 'ar': 'مرفوض'}
        }
        return status_map.get(self.status, {}).get(language, self.status)
    
    def to_dict(self, language='en'):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "method": self.method,
            "method_display": self.get_method_display(language),
            "amount": float(self.amount),
            "status": self.status,
            "status_display": self.get_status_display(language),
            "screenshot_url": self.screenshot_url,
            "transaction_id": self.transaction_id,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Cart(db.Model):
    __tablename__ = 'cart'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), nullable=False)  # For guest users
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # For logged-in users
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    menu_item = db.relationship('MenuItem', backref='cart_items')
    user = db.relationship('User', backref='cart_items')
    
    def to_dict(self, language='en'):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "menu_item_id": self.menu_item_id,
            "quantity": self.quantity,
            "notes": self.notes,
            "menu_item": self.menu_item.to_dict(language) if self.menu_item else None,
            "total_price": float(self.menu_item.price * self.quantity) if self.menu_item else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class SystemSettings(db.Model):
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_value(cls, key, default=None):
        """Get setting value by key"""
        setting = cls.query.filter_by(key=key).first()
        return setting.value if setting else default
    
    @classmethod
    def set_value(cls, key, value, description=None):
        """Set setting value by key"""
        setting = cls.query.filter_by(key=key).first()
        if setting:
            setting.value = value
            if description:
                setting.description = description
        else:
            setting = cls(key=key, value=value, description=description)
            db.session.add(setting)
        db.session.commit()
        return setting
