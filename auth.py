from functools import wraps
from flask import request, jsonify, session, redirect, url_for
from models import User
from extensions import db


def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in via session
        if 'user_id' not in session:
            return jsonify({"ok": False, "error": "Authentication required"}), 401
        
        user = User.query.get(session['user_id'])
        
        if not user:
            session.clear()
            return jsonify({"ok": False, "error": "Invalid session"}), 401
            
        return f(*args, **kwargs)
    return decorated_function


def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"ok": False, "error": "Authentication required"}), 401
        
        user = User.query.get(session['user_id'])
        
        if not user or not user.is_admin:
            return jsonify({"ok": False, "error": "Admin access required"}), 403
            
        return f(*args, **kwargs)
    return decorated_function


def require_auth_page(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('signin'))
        return f(*args, **kwargs)
    return decorated_function


def require_admin_page(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('signin'))
        if not session.get('is_admin'):
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


def login_user(user_dict):
    """Store user in session"""
    session['user_id'] = user_dict['id']
    session['is_admin'] = user_dict['is_admin']
    session.permanent = True


def logout_user():
    """Clear user session"""
    session.clear()


def get_current_user():
    """Get current logged in user"""
    if 'user_id' not in session:
        return None
    
    user = User.query.get(session['user_id'])
    return user.to_dict() if user else None


def get_current_language():
    """Get current language preference"""
    return session.get('language', 'en')
