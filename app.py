# app.py

from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, Branch, Product, Stock, CartItem, Order, OrderItem
from forms import RegistrationForm, LoginForm, QuantityForm, CheckoutForm

import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'this-should-be-a-secret-key'  # Replace with a real secret in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///medical_shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.before_first_request
def create_tables():
    db.create_all()
    # Optionally, populate with some sample data if empty
    if not Branch.query.first():
        # Create two sample branches
        b1 = Branch(name='Main Street Pharmacy', address='123 Main St, Cityville', phone='123-456-7890')
        b2 = Branch(name='Downtown Pharmacy', address='456 Elm Rd, Cityville', phone='098-765-4321')
        db.session.add_all([b1, b2])
        db.session.commit()

    if not Product.query.first():
        # Create sample products
        p1 = Product(name='Paracetamol 500mg', brand='MediCare', category='Pain Relief',
                     description='Paracetamol is used to treat mild to moderate pain.', price=30.0, image_filename=None)
        p2 = Product(name='Multivitamin Tablets', brand='HealthPlus', category='Vitamins',
                     description='Daily multivitamin to supplement nutrients.', price=150.0, image_filename=None)
        db.session.add_all([p1, p2])
        db.session.commit()

        # Create stock entries for each branch
        b1, b2 = Branch.query.all()
        stock1 = Stock(branch_id=b1.id, product_id=p1.id, quantity=50)
        stock2 = Stock(branch_id=b1.id, product_id=p2.id, quantity=20)
        stock3 = Stock(branch_id=b2.id, product_id=p1.id, quantity=30)
        stock4 = Stock(branch_id=b2.id, product_id=p2.id, quantity=10)
        db.session.add_all([stock1, stock2, stock3, stock4])
        db.session.commit()


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/branches')
def branches():
    all_branches = Branch.query.all()
    return render_template('branches.html', branches=all_branches)


@app.route('/select_branch/<int:branch_id>')
def select_branch(branch_id):
    branch = Branch.query.get_or_404(branch_id)
    session['selected_branch'] = branch_id
    flash(f'You have selected branch: {branch.name}', 'info')
    return redirect(url_for('catalog'))


@app.route('/catalog')
def catalog():
    # Ensure a branch is selected
    branch_id = session.get('selected_branch')
    if not branch_id:
        flash('Please select a branch first.', 'warning')
        return redirect(url_for('branches'))

    # Basic listing of all products with stock in this branch
    products = Product.query.all()
    branch = Branch.query.get(branch_id)

    # For each product, find stock quantity in this branch
    product_list = []
    for p in products:
        stock_entry = Stock.query.filter_by(branch_id=branch_id, product_id=p.id).first()
        qty = stock_entry.quantity if stock_entry else 0
        product_list.append({'product': p, 'stock_qty': qty})

    return render_template('catalog.html', products=product_list, branch=branch)


@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product_detail(product_id):
    branch_id = session.get('selected_branch')
    if not branch_id:
        flash('Please select a branch first.', 'warning')
        return redirect(url_for('branches'))

    product = Product.query.get_or_404(product_id)
    branch = Branch.query.get(branch_id)
    stock_entry = Stock.query.filter_by(branch_id=branch_id, product_id=product_id).first()
    available_qty = stock_entry.quantity if stock_entry else 0

    form = QuantityForm()
    if form.validate_on_submit():
        qty = form.quantity.data
        if qty > available_qty:
            flash(f'Only {available_qty} units available in this branch.', 'danger')
            return redirect(url_for('product_detail', product_id=product_id))

        # Add to cart (or update if already exists)
        existing = CartItem.query.filter_by(user_id=current_user.id,
                                            product_id=product_id,
                                            branch_id=branch_id).first()
        if existing:
            existing.quantity += qty
        else:
            new_item = CartItem(user_id=current_user.id,
                                product_id=product_id,
                                branch_id=branch_id,
                                quantity=qty)
            db.session.add(new_item)
        db.session.commit()
        flash('Added to cart!', 'success')
        return redirect(url_for('cart'))

    return render_template('product_detail.html',
                           product=product,
                           branch=branch,
                           available_qty=available_qty,
                           form=form)


@app.route('/cart', methods=['GET', 'POST'])
@login_required
def cart():
    branch_id = session.get('selected_branch')
    if not branch_id:
        flash('Please select a branch first.', 'warning')
        return redirect(url_for('branches'))

    # Fetch all cart items for this user and this branch
    items = CartItem.query.filter_by(user_id=current_user.id, branch_id=branch_id).all()
    total_amount = sum(item.product.price * item.quantity for item in items)

    # Handle quantity updates if needed
    if request.method == 'POST':
        for item in items:
            form_field = f'qty_{item.id}'
            if form_field in request.form:
                try:
                    new_qty = int(request.form.get(form_field))
                except ValueError:
                    continue
                # Check stock
                stock_entry = Stock.query.filter_by(branch_id=branch_id, product_id=item.product_id).first()
                available = stock_entry.quantity if stock_entry else 0
                if new_qty <= 0:
                    db.session.delete(item)
                elif new_qty <= available:
                    item.quantity = new_qty
                else:
                    flash(f'Cannot set quantity higher than {available} for {item.product.name}.', 'danger')
        db.session.commit()
        return redirect(url_for('cart'))

    return render_template('cart.html', items=items, total_amount=total_amount)


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    branch_id = session.get('selected_branch')
    if not branch_id:
        flash('Please select a branch first.', 'warning')
        return redirect(url_for('branches'))

    form = CheckoutForm()
    items = CartItem.query.filter_by(user_id=current_user.id, branch_id=branch_id).all()
    if not items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('catalog'))

    if form.validate_on_submit():
        # Create Order
        order = Order(user_id=current_user.id, branch_id=branch_id, status='Pending')
        db.session.add(order)
        db.session.commit()  # to get order.id

        # For each cart item, create OrderItem and reduce stock
        for ci in items:
            oi = OrderItem(order_id=order.id,
                           product_id=ci.product_id,
                           quantity=ci.quantity,
                           unit_price=ci.product.price)
            db.session.add(oi)
            # Reduce stock
            stock_entry = Stock.query.filter_by(branch_id=branch_id, product_id=ci.product_id).first()
            if stock_entry:
                stock_entry.quantity -= ci.quantity
            # Remove cart item
            db.session.delete(ci)
        db.session.commit()
        flash(f'Order placed! Your Order ID is {order.id}.', 'success')
        return redirect(url_for('orders'))

    total_amount = sum(item.product.price * item.quantity for item in items)
    return render_template('checkout.html', items=items, total_amount=total_amount, form=form)


@app.route('/orders')
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.timestamp.desc()).all()
    return render_template('orders.html', orders=user_orders)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pwd = generate_password_hash(form.password.data)
        new_user = User(name=form.name.data,
                        email=form.email.data.lower(),
                        password_hash=hashed_pwd)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash('Logged in successfully.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


if __name__ == '__main__':
    # If running locally: set FLASK_APP=app.py and then flask run.
    app.run(debug=True)
