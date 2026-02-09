from flask import Blueprint, jsonify, request, session
from flask_cors import cross_origin
from werkzeug.security import check_password_hash, generate_password_hash

from models import User
from auth import login_user, logout_user, get_current_user
from extensions import db

auth_api = Blueprint("auth_api", __name__)


def _bad_request(message: str, status_code: int = 400):
    return jsonify({"ok": False, "error": message}), status_code


@auth_api.post("/auth/register")
@cross_origin()
def register():
    try:
        data = request.get_json(silent=True) or {}
        
        required = ["name", "email", "password"]
        missing = [k for k in required if not data.get(k)]
        if missing:
            return _bad_request(f"Missing fields: {', '.join(missing)}")
        
        email = data["email"].strip().lower()
        phone = data.get("phone", "").strip()

        print(f"Register attempt: {email}, {phone}")

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f"User already exists: {existing_user.email}")
            return _bad_request("Email already registered", 409)
        
        if phone and User.query.filter_by(phone=phone).first():
            return _bad_request("Phone already registered", 409)
        
        # Create new user
        user = User(
            name=data["name"].strip(),
            email=email,
            phone=phone,
            password_hash=generate_password_hash(data["password"])
        )
        
        print(f"Creating user: {user.name}, {user.email}")
        
        db.session.add(user)
        db.session.commit()
        
        print(f"User saved with ID: {user.id}")
        
        user_dict = user.to_dict()
        login_user(user_dict)
        
        return jsonify({
            "ok": True,
            "user": user_dict
        })
    except Exception as e:
        print(f"Error in register: {e}")
        db.session.rollback()
        return _bad_request(f"Registration failed: {str(e)}"), 500


@auth_api.post("/auth/login")
@cross_origin()
def login():
    data = request.get_json(silent=True) or {}
    
    email = data.get("email", "").strip()
    password = data.get("password", "")
    
    if not email or not password:
        return _bad_request("Email and password required")
    
    user = User.query.filter_by(email=email.lower()).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return _bad_request("Invalid email or password", 401)
    
    user_dict = user.to_dict()
    login_user(user_dict)
    
    return jsonify({
        "ok": True,
        "user": user_dict
    })


@auth_api.post("/auth/logout")
@cross_origin()
def logout():
    logout_user()
    return jsonify({"ok": True})


@auth_api.get("/auth/me")
@cross_origin()
def get_current_user_info():
    user = get_current_user()
    if not user:
        return _bad_request("Not authenticated", 401)
    
    return jsonify({
        "ok": True,
        "user": user
    })


@auth_api.post("/auth/forgot-password")
@cross_origin()
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    
    if not email:
        return _bad_request("Email required")
    
    user = User.query.filter_by(email=email).first()
    if not user:
        return _bad_request("Email not found", 404)
    
    # TODO: Implement password reset email functionality
    # For now, just return success
    return jsonify({
        "ok": True,
        "message": "Password reset instructions sent to your email"
    })


@auth_api.post("/auth/reset-password")
@cross_origin()
def reset_password():
    data = request.get_json(silent=True) or {}
    
    required = ["token", "new_password"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        return _bad_request(f"Missing fields: {', '.join(missing)}")
    
    # TODO: Implement password reset token validation
    # For now, just return success
    return jsonify({
        "ok": True,
        "message": "Password reset successfully"
    })
