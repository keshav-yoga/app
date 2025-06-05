

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    # Relationship: user’s orders
    orders = db.relationship('Order', backref='customer', lazy=True)

    def __repr__(self):
        return f'<User {self.email}>'


class Branch(db.Model):
    __tablename__ = 'branches'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    # Relationship: branch stock & orders
    stocks = db.relationship('Stock', backref='branch', lazy=True)
    orders = db.relationship('Order', backref='branch', lazy=True)

    def __repr__(self):
        return f'<Branch {self.name}>'


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    brand = db.Column(db.String(100), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    image_filename = db.Column(db.String(100), nullable=True)
    # Relationship: stock per branch
    stocks = db.relationship('Stock', backref='product', lazy=True)
    # Relationship: order items
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

    def __repr__(self):
        return f'<Product {self.name}>'


class Stock(db.Model):
    __tablename__ = 'stocks'
    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f'<Stock Branch:{self.branch_id} Product:{self.product_id} Qty:{self.quantity}>'


class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    user = db.relationship('User', backref='cart_items')
    product = db.relationship('Product')
    branch = db.relationship('Branch')

    def __repr__(self):
        return f'<CartItem User:{self.user_id} Product:{self.product_id} Branch:{self.branch_id} Qty:{self.quantity}>'


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='Pending')
    # Relationship: order items
    items = db.relationship('OrderItem', backref='order', lazy=True)

    def __repr__(self):
        return f'<Order {self.id} User:{self.user_id} Branch:{self.branch_id}>'


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<OrderItem Order:{self.order_id} Product:{self.product_id} Qty:{self.quantity}>'
