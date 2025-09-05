# app.py
from flask import Flask, jsonify, request
from config import Config
from models import db, User, Product, Cart, CartItem, Order, OrderItem
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
from datetime import datetime, timezone


app = Flask(__name__)
app.config.from_object(Config)

# Ensure JWT secret exists
app.config.setdefault("JWT_SECRET_KEY", "super-secret")
jwt = JWTManager(app)

# Initialize database
db.init_app(app)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Welcome to the Capstone Project E-commerce Store API"})


# Registration endpoint
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"error": "Username and password required"}), 400

    existing_user = User.query.filter_by(username=data["username"]).first()
    if existing_user:
        return jsonify({"error": "User already exists"}), 400

    hashed_password = generate_password_hash(data["password"])
    new_user = User(username=data["username"], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully!"}), 201


# Login endpoint
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Username and password required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"message": "Invalid credentials"}), 401

    # Create a JWT token
    access_token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": access_token}), 200


# ADMIN-only: Create product
@app.route('/products', methods=['POST'])
@jwt_required()
def create_product():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({"error": "Admin privileges required"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    name = data.get('name')
    price = data.get('price')
    stock = data.get('stock', 0)
    description = data.get('description', '')

    if not name or price is None:
        return jsonify({"error": "Product 'name' and 'price' are required"}), 400

    # Basic type validation
    try:
        price = float(price)
        stock = int(stock)
    except (ValueError, TypeError):
        return jsonify({"error": "Price must be a number and stock must be an integer"}), 400

    product = Product(name=name, description=description, price=price, stock=stock)
    db.session.add(product)
    db.session.commit()

    return jsonify({
        "message": "Product created",
        "product": {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "stock": product.stock
        }
    }), 201


# Public: List products
@app.route('/products', methods=['GET'])
def list_products():
    products = Product.query.all()
    output = []
    for p in products:
        output.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "stock": p.stock,
            "created_at": p.created_at.isoformat()
        })
    return jsonify({"products": output}), 200


# Add product to cart
@app.route('/cart', methods=['POST'])
@jwt_required()
def add_to_cart():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not product_id:
        return jsonify({"error": "product_id is required"}), 400

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    # Get or create active cart for user
    cart = Cart.query.filter_by(user_id=current_user_id, status='active').first()
    if not cart:
        cart = Cart(user_id=current_user_id)
        db.session.add(cart)
        db.session.commit()

    # Check if item already in cart
    item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
    if item:
        item.quantity += quantity
    else:
        item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
        db.session.add(item)

    db.session.commit()

    return jsonify({
        "message": "Product added to cart",
        "cart_id": cart.id,
        "items": [
            {
                "product_id": ci.product_id,
                "name": ci.product.name,
                "quantity": ci.quantity,
                "price": ci.product.price
            } for ci in cart.items
        ]
    }), 200


# Checkout endpoint
@app.route('/checkout', methods=['POST'])
@jwt_required()
def checkout():
    current_user_id = get_jwt_identity()

    # Get the active cart
    cart = Cart.query.filter_by(user_id=current_user_id, status='active').first()
    if not cart or not cart.items:
        return jsonify({"error": "No active cart or cart is empty"}), 400

    # Check stock availability first
    for ci in cart.items:
        if ci.quantity > ci.product.stock:
            return jsonify({"error": f"Not enough stock for {ci.product.name}"}), 400

    # Create an order
    order = Order(user_id=current_user_id)
    db.session.add(order)

    # Move items from cart to order and reduce stock
    for ci in cart.items:
        order_item = OrderItem(
            order=order,
            product_id=ci.product_id,
            quantity=ci.quantity,
            price=ci.product.price
        )
        ci.product.stock -= ci.quantity
        db.session.add(order_item)

    # Mark cart as checked out
    cart.status = 'checked_out'
    db.session.commit()

    return jsonify({
        "message": "Checkout successful",
        "order_id": order.id,
        "items": [
            {
                "product_id": oi.product_id,
                "name": oi.product.name,
                "quantity": oi.quantity,
                "price": oi.price
            } for oi in order.items
        ]
    }), 200


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # creates tables
    app.run(debug=True)

