from flask import Blueprint, jsonify, request, session
from flask_cors import cross_origin
from werkzeug.utils import secure_filename
import os
from datetime import datetime

from extensions import db
from models import Payment, Order, SystemSettings
from auth import require_auth, require_admin, get_current_user, get_current_language
from config import Config

payments_api = Blueprint("payments_api", __name__)


def _bad_request(message: str, status_code: int = 400):
    return jsonify({"ok": False, "error": message}), status_code


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


@payments_api.get("/payments/methods")
@cross_origin()
def get_payment_methods():
    """Get available payment methods"""
    language = get_current_language()
    
    methods = [
        {
            "id": "instapay",
            "name": "Instapay" if language == 'en' else "إنستاباي",
            "instructions": "Send payment to our Instapay number: 01012345678" if language == 'en' else "أرسل الدفع إلى رقم إنستاباي: 01012345678",
            "number": "01012345678"
        },
        {
            "id": "vodafone_cash",
            "name": "Vodafone Cash" if language == 'en' else "فودافون كاش",
            "instructions": "Send payment to our Vodafone Cash number: 01012345678" if language == 'en' else "أرسل الدفع إلى رقم فودافون كاش: 01012345678",
            "number": "01012345678"
        },
        {
            "id": "orange_money",
            "name": "Orange Money" if language == 'en' else "أورانج موني",
            "instructions": "Send payment to our Orange Money number: 01012345678" if language == 'en' else "أرسل الدفع إلى رقم أورانج موني: 01012345678",
            "number": "01012345678"
        },
        {
            "id": "etisalat_wallet",
            "name": "Etisalat Wallet" if language == 'en' else "محفظة اتصالات",
            "instructions": "Send payment to our Etisalat Wallet number: 01012345678" if language == 'en' else "أرسل الدفع إلى رقم محفظة اتصالات: 01012345678",
            "number": "01012345678"
        },
        {
            "id": "cod",
            "name": "Cash on Delivery" if language == 'en' else "الدفع عند الاستلام",
            "instructions": "Pay cash when your order arrives" if language == 'en' else "ادفع نقداً عند وصول طلبك",
            "number": None
        }
    ]
    
    return jsonify({
        "ok": True,
        "methods": methods
    })


@payments_api.post("/payments")
@cross_origin()
@require_auth
def create_payment():
    user_id = session['user_id']
    data = request.get_json(silent=True) or {}
    
    required = ["order_id", "method"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        return _bad_request(f"Missing fields: {', '.join(missing)}")
    
    order_id = int(data["order_id"])
    method = data["method"]
    notes = data.get("notes", "").strip()
    
    # Validate payment method
    valid_methods = ['instapay', 'vodafone_cash', 'orange_money', 'etisalat_wallet', 'cod']
    if method not in valid_methods:
        return _bad_request(f"Invalid payment method. Must be one of: {', '.join(valid_methods)}")
    
    # Get order
    order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not order:
        return _bad_request("Order not found", 404)
    
    # Check if payment already exists for this order
    existing_payment = Payment.query.filter_by(order_id=order_id).first()
    if existing_payment:
        return _bad_request("Payment already exists for this order", 409)
    
    # Create payment record
    payment = Payment(
        order_id=order_id,
        method=method,
        amount=order.advance_amount,
        status='pending',
        notes=notes
    )
    
    db.session.add(payment)
    db.session.commit()
    
    language = get_current_language()
    return jsonify({
        "ok": True,
        "payment": payment.to_dict(language),
        "message": "Payment record created. Please upload payment proof."
    }), 201


@payments_api.post("/payments/<int:payment_id>/upload")
@cross_origin()
@require_auth
def upload_payment_proof(payment_id: int):
    user_id = session['user_id']
    
    # Get payment
    payment = Payment.query.join(Order).filter(
        Payment.id == payment_id,
        Order.user_id == user_id
    ).first()
    
    if not payment:
        return _bad_request("Payment not found", 404)
    
    if 'screenshot' not in request.files:
        return _bad_request("No file uploaded")
    
    file = request.files['screenshot']
    if file.filename == '':
        return _bad_request("No file selected")
    
    if not allowed_file(file.filename):
        return _bad_request(f"File type not allowed. Allowed types: {', '.join(Config.ALLOWED_EXTENSIONS)}")
    
    # Save file
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"payment_{payment_id}_{timestamp}_{filename}"
    
    upload_path = os.path.join(Config.UPLOAD_FOLDER, 'payments')
    os.makedirs(upload_path, exist_ok=True)
    
    file_path = os.path.join(upload_path, filename)
    file.save(file_path)
    
    # Update payment record
    payment.screenshot_url = f"/static/uploads/payments/{filename}"
    payment.status = 'pending'  # Reset to pending when new proof uploaded
    db.session.commit()
    
    language = get_current_language()
    return jsonify({
        "ok": True,
        "payment": payment.to_dict(language),
        "message": "Payment proof uploaded successfully"
    })


@payments_api.put("/payments/<int:payment_id>/confirm")
@cross_origin()
@require_admin
def confirm_payment(payment_id: int):
    payment = Payment.query.get(payment_id)
    if not payment:
        return _bad_request("Payment not found", 404)
    
    data = request.get_json(silent=True) or {}
    transaction_id = data.get("transaction_id", "").strip()
    notes = data.get("notes", "").strip()
    
    payment.status = 'confirmed'
    if transaction_id:
        payment.transaction_id = transaction_id
    if notes:
        payment.notes = notes
    
    # Update order status to confirmed if payment is confirmed
    order = payment.order
    if order.status == 'new':
        order.status = 'confirmed'
    
    db.session.commit()
    
    language = get_current_language()
    return jsonify({
        "ok": True,
        "payment": payment.to_dict(language),
        "order": order.to_dict(language),
        "message": "Payment confirmed successfully"
    })


@payments_api.put("/payments/<int:payment_id>/reject")
@cross_origin()
@require_admin
def reject_payment(payment_id: int):
    payment = Payment.query.get(payment_id)
    if not payment:
        return _bad_request("Payment not found", 404)
    
    data = request.get_json(silent=True) or {}
    notes = data.get("notes", "").strip()
    
    if not notes:
        return _bad_request("Rejection reason required")
    
    payment.status = 'rejected'
    payment.notes = notes
    
    db.session.commit()
    
    language = get_current_language()
    return jsonify({
        "ok": True,
        "payment": payment.to_dict(language),
        "message": "Payment rejected"
    })


@payments_api.get("/admin/payments")
@cross_origin()
@require_admin
def get_all_payments():
    language = get_current_language()
    
    # Get query parameters
    status = request.args.get('status')
    method = request.args.get('method')
    
    query = Payment.query
    
    # Apply filters
    if status:
        query = query.filter_by(status=status)
    
    if method:
        query = query.filter_by(method=method)
    
    payments = query.order_by(Payment.created_at.desc()).all()
    
    return jsonify({
        "ok": True,
        "payments": [payment.to_dict(language) for payment in payments]
    })


@payments_api.get("/admin/payments/pending")
@cross_origin()
@require_admin
def get_pending_payments():
    """Get pending payments that need admin approval"""
    language = get_current_language()
    
    pending_payments = Payment.query.filter_by(status='pending').order_by(Payment.created_at.desc()).all()
    
    return jsonify({
        "ok": True,
        "payments": [payment.to_dict(language) for payment in pending_payments]
    })


@payments_api.get("/payments/order/<int:order_id>")
@cross_origin()
@require_auth
def get_order_payments(order_id: int):
    user_id = session['user_id']
    language = get_current_language()
    
    # Verify order belongs to user
    order = Order.query.filter_by(id=order_id, user_id=user_id).first()
    if not order:
        return _bad_request("Order not found", 404)
    
    payments = Payment.query.filter_by(order_id=order_id).all()
    
    return jsonify({
        "ok": True,
        "payments": [payment.to_dict(language) for payment in payments]
    })


@payments_api.get("/admin/payments/stats")
@cross_origin()
@require_admin
def get_payment_stats():
    # Get query parameters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    query = Payment.query
    
    # Apply date filters
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Payment.created_at >= date_from)
        except ValueError:
            return _bad_request("Invalid date_from format. Use YYYY-MM-DD")
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(Payment.created_at <= date_to)
        except ValueError:
            return _bad_request("Invalid date_to format. Use YYYY-MM-DD")
    
    # Calculate stats
    total_payments = query.count()
    confirmed_payments = query.filter_by(status='confirmed').count()
    pending_payments = query.filter_by(status='pending').count()
    rejected_payments = query.filter_by(status='rejected').count()
    
    total_amount = sum(payment.amount for payment in query.filter_by(status='confirmed').all())
    
    # Payments by method
    method_counts = {}
    for method in ['instapay', 'vodafone_cash', 'orange_money', 'etisalat_wallet', 'cod']:
        count = query.filter_by(method=method).count()
        method_counts[method] = count
    
    return jsonify({
        "ok": True,
        "stats": {
            "total_payments": total_payments,
            "confirmed_payments": confirmed_payments,
            "pending_payments": pending_payments,
            "rejected_payments": rejected_payments,
            "total_amount": float(total_amount),
            "method_counts": method_counts
        }
    })
