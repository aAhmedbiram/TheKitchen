from flask import Blueprint, jsonify, request, session
from flask_cors import cross_origin

from extensions import db
from models import Cart, MenuItem
from auth import require_auth, get_current_user, get_current_language

cart_api = Blueprint("cart_api", __name__)


def _bad_request(message: str, status_code: int = 400):
    return jsonify({"ok": False, "error": message}), status_code


def get_session_id():
    """Get or create session ID for guest users"""
    if 'cart_session_id' not in session:
        session['cart_session_id'] = str(session.get('_id', ''))
    return session['cart_session_id']


def get_cart_items():
    """Get cart items for current user (logged in or guest)"""
    language = get_current_language()
    
    if 'user_id' in session:
        # Logged in user
        cart_items = Cart.query.filter_by(user_id=session['user_id']).all()
    else:
        # Guest user
        session_id = get_session_id()
        cart_items = Cart.query.filter_by(session_id=session_id).all()
    
    return [item.to_dict(language) for item in cart_items]


@cart_api.get("/cart")
@cross_origin()
def get_cart():
    cart_items = get_cart_items()
    
    # Calculate totals
    subtotal = sum(item['total_price'] for item in cart_items)
    total_items = sum(item['quantity'] for item in cart_items)
    
    return jsonify({
        "ok": True,
        "items": cart_items,
        "subtotal": subtotal,
        "total_items": total_items
    })


@cart_api.post("/cart")
@cross_origin()
def add_to_cart():
    data = request.get_json(silent=True) or {}
    
    required = ["menu_item_id", "quantity"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        return _bad_request(f"Missing fields: {', '.join(missing)}")
    
    menu_item_id = int(data["menu_item_id"])
    quantity = int(data["quantity"])
    notes = data.get("notes", "").strip()
    
    if quantity <= 0:
        return _bad_request("Quantity must be greater than 0")
    
    # Check if menu item exists and is available
    menu_item = MenuItem.query.get(menu_item_id)
    if not menu_item:
        return _bad_request("Menu item not found", 404)
    
    if not menu_item.is_available:
        return _bad_request("Menu item is not available", 400)
    
    # Determine cart owner (user or session)
    user_id = session.get('user_id')
    session_id = get_session_id() if not user_id else None
    
    # Check if item already exists in cart
    existing_item = None
    if user_id:
        existing_item = Cart.query.filter_by(
            user_id=user_id, 
            menu_item_id=menu_item_id
        ).first()
    else:
        existing_item = Cart.query.filter_by(
            session_id=session_id, 
            menu_item_id=menu_item_id
        ).first()
    
    if existing_item:
        # Update quantity
        existing_item.quantity += quantity
        if notes:
            existing_item.notes = notes
    else:
        # Add new item
        cart_item = Cart(
            user_id=user_id,
            session_id=session_id,
            menu_item_id=menu_item_id,
            quantity=quantity,
            notes=notes
        )
        db.session.add(cart_item)
    
    db.session.commit()
    
    cart_items = get_cart_items()
    subtotal = sum(item['total_price'] for item in cart_items)
    total_items = sum(item['quantity'] for item in cart_items)
    
    return jsonify({
        "ok": True,
        "message": "Item added to cart",
        "items": cart_items,
        "subtotal": subtotal,
        "total_items": total_items
    })


@cart_api.put("/cart/<int:item_id>")
@cross_origin()
def update_cart_item(item_id: int):
    data = request.get_json(silent=True) or {}
    
    quantity = data.get("quantity")
    notes = data.get("notes", "").strip()
    
    if quantity is None:
        return _bad_request("Quantity required")
    
    quantity = int(quantity)
    if quantity <= 0:
        return _bad_request("Quantity must be greater than 0")
    
    # Get cart item
    cart_item = Cart.query.get(item_id)
    if not cart_item:
        return _bad_request("Cart item not found", 404)
    
    # Check ownership
    user_id = session.get('user_id')
    if user_id:
        if cart_item.user_id != user_id:
            return _bad_request("Access denied", 403)
    else:
        session_id = get_session_id()
        if cart_item.session_id != session_id:
            return _bad_request("Access denied", 403)
    
    # Update item
    cart_item.quantity = quantity
    if notes:
        cart_item.notes = notes
    
    db.session.commit()
    
    cart_items = get_cart_items()
    subtotal = sum(item['total_price'] for item in cart_items)
    total_items = sum(item['quantity'] for item in cart_items)
    
    return jsonify({
        "ok": True,
        "message": "Cart item updated",
        "items": cart_items,
        "subtotal": subtotal,
        "total_items": total_items
    })


@cart_api.delete("/cart/<int:item_id>")
@cross_origin()
def remove_from_cart(item_id: int):
    # Get cart item
    cart_item = Cart.query.get(item_id)
    if not cart_item:
        return _bad_request("Cart item not found", 404)
    
    # Check ownership
    user_id = session.get('user_id')
    if user_id:
        if cart_item.user_id != user_id:
            return _bad_request("Access denied", 403)
    else:
        session_id = get_session_id()
        if cart_item.session_id != session_id:
            return _bad_request("Access denied", 403)
    
    db.session.delete(cart_item)
    db.session.commit()
    
    cart_items = get_cart_items()
    subtotal = sum(item['total_price'] for item in cart_items)
    total_items = sum(item['quantity'] for item in cart_items)
    
    return jsonify({
        "ok": True,
        "message": "Item removed from cart",
        "items": cart_items,
        "subtotal": subtotal,
        "total_items": total_items
    })


@cart_api.delete("/cart")
@cross_origin()
def clear_cart():
    # Clear all cart items for current user/session
    user_id = session.get('user_id')
    
    if user_id:
        Cart.query.filter_by(user_id=user_id).delete()
    else:
        session_id = get_session_id()
        Cart.query.filter_by(session_id=session_id).delete()
    
    db.session.commit()
    
    return jsonify({
        "ok": True,
        "message": "Cart cleared",
        "items": [],
        "subtotal": 0,
        "total_items": 0
    })


@cart_api.post("/cart/merge")
@cross_origin()
@require_auth
def merge_cart():
    """Merge guest cart with user cart after login"""
    user_id = session['user_id']
    session_id = get_session_id()
    
    # Get guest cart items
    guest_items = Cart.query.filter_by(session_id=session_id).all()
    
    if not guest_items:
        return jsonify({
            "ok": True,
            "message": "No guest items to merge"
        })
    
    # Merge with user cart
    for guest_item in guest_items:
        # Check if item already exists in user cart
        existing_item = Cart.query.filter_by(
            user_id=user_id,
            menu_item_id=guest_item.menu_item_id
        ).first()
        
        if existing_item:
            # Add quantities
            existing_item.quantity += guest_item.quantity
            if guest_item.notes and not existing_item.notes:
                existing_item.notes = guest_item.notes
        else:
            # Transfer to user cart
            guest_item.user_id = user_id
            guest_item.session_id = None
    
    db.session.commit()
    
    cart_items = get_cart_items()
    subtotal = sum(item['total_price'] for item in cart_items)
    total_items = sum(item['quantity'] for item in cart_items)
    
    return jsonify({
        "ok": True,
        "message": "Cart merged successfully",
        "items": cart_items,
        "subtotal": subtotal,
        "total_items": total_items
    })
