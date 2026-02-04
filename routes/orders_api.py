from flask import Blueprint, jsonify, request, session
from flask_cors import cross_origin
from datetime import datetime

from extensions import db
from models import Order, OrderItem, Cart, MenuItem, SystemSettings
from auth import require_auth, require_admin, get_current_user, get_current_language
from config import Config

orders_api = Blueprint("orders_api", __name__)


def _bad_request(message: str, status_code: int = 400):
    return jsonify({"ok": False, "error": message}), status_code


@orders_api.get("/orders")
@cross_origin()
@require_auth
def get_user_orders():
    user_id = session['user_id']
    language = get_current_language()
    
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    return jsonify({
        "ok": True,
        "orders": [order.to_dict(language) for order in orders]
    })


@orders_api.get("/orders/<int:order_id>")
@cross_origin()
@require_auth
def get_order_detail(order_id: int):
    user_id = session['user_id']
    language = get_current_language()
    
    order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not order:
        return _bad_request("Order not found", 404)
    
    return jsonify({
        "ok": True,
        "order": order.to_dict(language)
    })


@orders_api.post("/orders")
@cross_origin()
@require_auth
def create_order():
    user_id = session['user_id']
    data = request.get_json(silent=True) or {}
    
    required = ["delivery_address"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        return _bad_request(f"Missing fields: {', '.join(missing)}")
    
    # Get cart items
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    if not cart_items:
        return _bad_request("Cart is empty")
    
    # Calculate subtotal
    subtotal = sum(item.menu_item.price * item.quantity for item in cart_items)
    
    # Get delivery fee (admin will set this later, use minimum for now)
    delivery_fee = Config.MIN_DELIVERY_FEE
    
    # Calculate totals
    total_amount = subtotal + delivery_fee
    advance_amount = total_amount * (Config.ADVANCE_PAYMENT_PERCENTAGE / 100)
    
    # Create order
    order = Order(
        user_id=user_id,
        status='new',
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total_amount=total_amount,
        advance_amount=advance_amount,
        delivery_address=data['delivery_address'].strip(),
        notes=data.get('notes', '').strip()
    )
    
    db.session.add(order)
    db.session.flush()  # Get order ID
    
    # Create order items
    for cart_item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=cart_item.menu_item_id,
            quantity=cart_item.quantity,
            unit_price=cart_item.menu_item.price,
            notes=cart_item.notes
        )
        db.session.add(order_item)
    
    # Clear cart
    Cart.query.filter_by(user_id=user_id).delete()
    
    db.session.commit()
    
    language = get_current_language()
    return jsonify({
        "ok": True,
        "order": order.to_dict(language),
        "message": "Order created successfully"
    }), 201


@orders_api.put("/orders/<int:order_id>/status")
@cross_origin()
@require_admin
def update_order_status(order_id: int):
    order = Order.query.get(order_id)
    if not order:
        return _bad_request("Order not found", 404)
    
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    admin_notes = data.get("admin_notes", "").strip()
    
    if not status:
        return _bad_request("Status required")
    
    valid_statuses = ['new', 'confirmed', 'preparing', 'on_way', 'delivered', 'cancelled']
    if status not in valid_statuses:
        return _bad_request(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    
    order.status = status
    if admin_notes:
        order.admin_notes = admin_notes
    
    db.session.commit()
    
    language = get_current_language()
    return jsonify({
        "ok": True,
        "order": order.to_dict(language),
        "message": f"Order status updated to {order.get_status_display(language)}"
    })


@orders_api.put("/orders/<int:order_id>/delivery-fee")
@cross_origin()
@require_admin
def update_delivery_fee(order_id: int):
    order = Order.query.get(order_id)
    if not order:
        return _bad_request("Order not found", 404)
    
    data = request.get_json(silent=True) or {}
    delivery_fee = data.get("delivery_fee")
    
    if delivery_fee is None:
        return _bad_request("Delivery fee required")
    
    try:
        delivery_fee = float(delivery_fee)
    except (TypeError, ValueError):
        return _bad_request("Invalid delivery fee")
    
    if delivery_fee < Config.MIN_DELIVERY_FEE or delivery_fee > Config.MAX_DELIVERY_FEE:
        return _bad_request(f"Delivery fee must be between {Config.MIN_DELIVERY_FEE} and {Config.MAX_DELIVERY_FEE} EGP")
    
    # Update order totals
    order.delivery_fee = delivery_fee
    order.total_amount = order.subtotal + delivery_fee
    order.advance_amount = order.total_amount * (Config.ADVANCE_PAYMENT_PERCENTAGE / 100)
    
    db.session.commit()
    
    language = get_current_language()
    return jsonify({
        "ok": True,
        "order": order.to_dict(language),
        "message": "Delivery fee updated"
    })


@orders_api.put("/orders/<int:order_id>/notes")
@cross_origin()
@require_admin
def update_order_notes(order_id: int):
    order = Order.query.get(order_id)
    if not order:
        return _bad_request("Order not found", 404)
    
    data = request.get_json(silent=True) or {}
    admin_notes = data.get("admin_notes", "")
    
    order.admin_notes = admin_notes.strip()
    db.session.commit()
    
    language = get_current_language()
    return jsonify({
        "ok": True,
        "order": order.to_dict(language),
        "message": "Order notes updated"
    })


@orders_api.get("/admin/orders")
@cross_origin()
@require_admin
def get_all_orders():
    language = get_current_language()
    
    # Get query parameters
    status = request.args.get('status')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    query = Order.query
    
    # Apply filters
    if status:
        query = query.filter_by(status=status)
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Order.created_at >= date_from)
        except ValueError:
            return _bad_request("Invalid date_from format. Use YYYY-MM-DD")
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(Order.created_at <= date_to)
        except ValueError:
            return _bad_request("Invalid date_to format. Use YYYY-MM-DD")
    
    orders = query.order_by(Order.created_at.desc()).all()
    
    return jsonify({
        "ok": True,
        "orders": [order.to_dict(language) for order in orders]
    })


@orders_api.post("/orders/<int:order_id>/reorder")
@cross_origin()
@require_auth
def reorder(order_id: int):
    user_id = session['user_id']
    language = get_current_language()
    
    # Get original order
    original_order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not original_order:
        return _bad_request("Order not found", 404)
    
    # Add items back to cart
    for order_item in original_order.items:
        # Check if item already exists in cart
        existing_cart_item = Cart.query.filter_by(
            user_id=user_id,
            menu_item_id=order_item.menu_item_id
        ).first()
        
        if existing_cart_item:
            existing_cart_item.quantity += order_item.quantity
        else:
            cart_item = Cart(
                user_id=user_id,
                menu_item_id=order_item.menu_item_id,
                quantity=order_item.quantity,
                notes=order_item.notes
            )
            db.session.add(cart_item)
    
    db.session.commit()
    
    # Get updated cart
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    cart_data = [item.to_dict(language) for item in cart_items]
    subtotal = sum(item['total_price'] for item in cart_data)
    total_items = sum(item['quantity'] for item in cart_data)
    
    return jsonify({
        "ok": True,
        "message": "Items added to cart",
        "items": cart_data,
        "subtotal": subtotal,
        "total_items": total_items
    })


@orders_api.get("/admin/orders/stats")
@cross_origin()
@require_admin
def get_order_stats():
    # Get query parameters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    query = Order.query
    
    # Apply date filters
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Order.created_at >= date_from)
        except ValueError:
            return _bad_request("Invalid date_from format. Use YYYY-MM-DD")
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(Order.created_at <= date_to)
        except ValueError:
            return _bad_request("Invalid date_to format. Use YYYY-MM-DD")
    
    # Calculate stats
    total_orders = query.count()
    total_revenue = sum(order.total_amount for order in query.all())
    
    # Orders by status
    status_counts = {}
    for status in ['new', 'confirmed', 'preparing', 'on_way', 'delivered', 'cancelled']:
        count = query.filter_by(status=status).count()
        status_counts[status] = count
    
    return jsonify({
        "ok": True,
        "stats": {
            "total_orders": total_orders,
            "total_revenue": float(total_revenue),
            "status_counts": status_counts
        }
    })
