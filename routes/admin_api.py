from flask import Blueprint, jsonify, request, session
from flask_cors import cross_origin
from datetime import datetime, timedelta

from extensions import db
from models import User, Order, MenuItem, Payment, SystemSettings
from auth import require_admin, get_current_language

admin_api = Blueprint("admin_api", __name__)


def _bad_request(message: str, status_code: int = 400):
    return jsonify({"ok": False, "error": message}), status_code


@admin_api.get("/admin/dashboard")
@cross_origin()
@require_admin
def get_dashboard_stats():
    """Get dashboard statistics"""
    language = get_current_language()
    
    # Time periods
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Orders stats
    total_orders = Order.query.count()
    orders_today = Order.query.filter(Order.created_at >= today).count()
    orders_this_week = Order.query.filter(Order.created_at >= week_ago).count()
    orders_this_month = Order.query.filter(Order.created_at >= month_ago).count()
    
    # Revenue stats
    total_revenue = sum(order.total_amount for order in Order.query.filter_by(status='delivered').all())
    revenue_today = sum(order.total_amount for order in Order.query.filter(
        Order.created_at >= today,
        Order.status == 'delivered'
    ).all())
    revenue_this_week = sum(order.total_amount for order in Order.query.filter(
        Order.created_at >= week_ago,
        Order.status == 'delivered'
    ).all())
    revenue_this_month = sum(order.total_amount for order in Order.query.filter(
        Order.created_at >= month_ago,
        Order.status == 'delivered'
    ).all())
    
    # Orders by status
    status_counts = {}
    for status in ['new', 'confirmed', 'preparing', 'on_way', 'delivered', 'cancelled']:
        count = Order.query.filter_by(status=status).count()
        status_counts[status] = count
    
    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # Pending payments
    pending_payments = Payment.query.filter_by(status='pending').count()
    
    # Menu items stats
    total_menu_items = MenuItem.query.count()
    available_menu_items = MenuItem.query.filter_by(is_available=True).count()
    
    # Customers stats
    total_customers = User.query.filter_by(is_admin=False).count()
    new_customers_this_month = User.query.filter(
        User.created_at >= month_ago,
        User.is_admin == False
    ).count()
    
    return jsonify({
        "ok": True,
        "stats": {
            "orders": {
                "total": total_orders,
                "today": orders_today,
                "this_week": orders_this_week,
                "this_month": orders_this_month,
                "by_status": status_counts
            },
            "revenue": {
                "total": float(total_revenue),
                "today": float(revenue_today),
                "this_week": float(revenue_this_week),
                "this_month": float(revenue_this_month)
            },
            "payments": {
                "pending": pending_payments
            },
            "menu": {
                "total_items": total_menu_items,
                "available_items": available_menu_items
            },
            "customers": {
                "total": total_customers,
                "new_this_month": new_customers_this_month
            }
        },
        "recent_orders": [order.to_dict(language) for order in recent_orders]
    })


@admin_api.get("/admin/customers")
@cross_origin()
@require_admin
def get_customers():
    """Get all customers"""
    language = get_current_language()
    
    customers = User.query.filter_by(is_admin=False).order_by(User.created_at.desc()).all()
    
    customer_data = []
    for customer in customers:
        customer_dict = customer.to_dict()
        # Add order count
        order_count = Order.query.filter_by(user_id=customer.id).count()
        total_spent = sum(order.total_amount for order in Order.query.filter_by(user_id=customer.id, status='delivered').all())
        
        customer_dict.update({
            "order_count": order_count,
            "total_spent": float(total_spent)
        })
        customer_data.append(customer_dict)
    
    return jsonify({
        "ok": True,
        "customers": customer_data
    })


@admin_api.get("/admin/customers/<int:customer_id>")
@cross_origin()
@require_admin
def get_customer_detail(customer_id: int):
    """Get customer details with orders"""
    language = get_current_language()
    
    customer = User.query.filter_by(id=customer_id, is_admin=False).first()
    if not customer:
        return _bad_request("Customer not found", 404)
    
    customer_dict = customer.to_dict()
    
    # Get customer orders
    orders = Order.query.filter_by(user_id=customer_id).order_by(Order.created_at.desc()).all()
    
    return jsonify({
        "ok": True,
        "customer": customer_dict,
        "orders": [order.to_dict(language) for order in orders]
    })


@admin_api.get("/admin/settings")
@cross_origin()
@require_admin
def get_settings():
    """Get system settings"""
    settings = SystemSettings.query.all()
    
    settings_dict = {}
    for setting in settings:
        settings_dict[setting.key] = {
            "value": setting.value,
            "description": setting.description
        }
    
    # Default settings if not in database
    default_settings = {
        "ordering_enabled": {"value": "true", "description": "Enable/disable ordering system"},
        "delivery_fee_min": {"value": "40", "description": "Minimum delivery fee in EGP"},
        "delivery_fee_max": {"value": "80", "description": "Maximum delivery fee in EGP"},
        "advance_percentage": {"value": "20", "description": "Advance payment percentage"},
        "phone_number": {"value": "01012345678", "description": "Contact phone number"},
        "email": {"value": "contact@thekitchen.com", "description": "Contact email"},
        "address": {"value": "Cairo, Egypt", "description": "Restaurant address"}
    }
    
    # Merge with defaults
    for key, default in default_settings.items():
        if key not in settings_dict:
            settings_dict[key] = default
    
    return jsonify({
        "ok": True,
        "settings": settings_dict
    })


@admin_api.put("/admin/settings")
@cross_origin()
@require_admin
def update_settings():
    """Update system settings"""
    data = request.get_json(silent=True) or {}
    
    updated_settings = {}
    
    for key, value in data.items():
        # Get description from existing setting or use default
        existing = SystemSettings.query.filter_by(key=key).first()
        description = existing.description if existing else key
        
        # Update or create setting
        SystemSettings.set_value(key, str(value), description)
        updated_settings[key] = str(value)
    
    return jsonify({
        "ok": True,
        "settings": updated_settings,
        "message": "Settings updated successfully"
    })


@admin_api.get("/admin/analytics")
@cross_origin()
@require_admin
def get_analytics():
    """Get detailed analytics"""
    # Get query parameters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    group_by = request.args.get('group_by', 'day')  # day, week, month
    
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
    
    orders = query.all()
    
    # Revenue over time
    revenue_data = {}
    for order in orders:
        if order.status == 'delivered':
            date_key = order.created_at.date().isoformat()
            if date_key not in revenue_data:
                revenue_data[date_key] = 0
            revenue_data[date_key] += float(order.total_amount)
    
    # Top selling items
    item_sales = {}
    for order in orders:
        for item in order.items:
            item_name = item.menu_item.get_name('en')
            if item_name not in item_sales:
                item_sales[item_name] = {"quantity": 0, "revenue": 0}
            item_sales[item_name]["quantity"] += item.quantity
            item_sales[item_name]["revenue"] += float(item.total_price)
    
    # Sort by revenue
    top_items = sorted(item_sales.items(), key=lambda x: x[1]["revenue"], reverse=True)[:10]
    
    # Payment methods usage
    payment_methods = {}
    for order in orders:
        for payment in order.payments:
            method = payment.method
            if method not in payment_methods:
                payment_methods[method] = {"count": 0, "amount": 0}
            payment_methods[method]["count"] += 1
            payment_methods[method]["amount"] += float(payment.amount)
    
    return jsonify({
        "ok": True,
        "analytics": {
            "revenue_over_time": revenue_data,
            "top_items": [{"name": name, **stats} for name, stats in top_items],
            "payment_methods": payment_methods,
            "summary": {
                "total_orders": len(orders),
                "total_revenue": sum(float(order.total_amount) for order in orders if order.status == 'delivered'),
                "average_order_value": sum(float(order.total_amount) for order in orders if order.status == 'delivered') / len([o for o in orders if o.status == 'delivered']) if orders else 0
            }
        }
    })


@admin_api.post("/admin/toggle-ordering")
@cross_origin()
@require_admin
def toggle_ordering():
    """Toggle ordering system on/off"""
    current_status = SystemSettings.get_value("ordering_enabled", "true")
    new_status = "false" if current_status == "true" else "true"
    
    SystemSettings.set_value("ordering_enabled", new_status, "Enable/disable ordering system")
    
    return jsonify({
        "ok": True,
        "ordering_enabled": new_status == "true",
        "message": f"Ordering system {'enabled' if new_status == 'true' else 'disabled'}"
    })


@admin_api.get("/admin/ordering-status")
@cross_origin()
def get_ordering_status():
    """Get current ordering system status"""
    ordering_enabled = SystemSettings.get_value("ordering_enabled", "true") == "true"
    
    return jsonify({
        "ok": True,
        "ordering_enabled": ordering_enabled
    })
